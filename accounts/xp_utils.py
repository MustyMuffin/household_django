class XPManager:
    _cached_settings = None

    @classmethod
    def get_settings(cls):
        if cls._cached_settings is None:
            from accounts.models import XPSettings

            try:
                cls._cached_settings = XPSettings.objects.first()
                if not cls._cached_settings:
                    raise XPSettings.DoesNotExist
            except XPSettings.DoesNotExist:
                class DummySettings:
                    base = 50
                    exponent = 0.75
                cls._cached_settings = DummySettings()

        return cls._cached_settings.base, cls._cached_settings.exponent

    @staticmethod
    def xp_for_level(level):
        base, exponent = XPManager.get_settings()
        xp_required = int(base * (level ** exponent))

        print(f"[DEBUG] xp_for_level({level}): base={base}, exponent={exponent}, calculated_xp={xp_required}")

        return xp_required

    @staticmethod
    def level_from_xp(xp):
        base, exponent = XPManager.get_settings()

        print(f"[DEBUG] level_from_xp({xp}): base={base}, exponent={exponent}")

        if xp <= 0:
            print("[DEBUG] XP <= 0, returning level 1")

        calculated_level = max(1, int((xp / base) ** (1 / exponent)))

        print(f"[DEBUG] xp={xp}, calculated_level={calculated_level}")

        return calculated_level

    @staticmethod
    def next_level_xp(level):
        return XPManager.xp_for_level(level + 1)

    @staticmethod
    def progress_percent(xp, level):
        print(f"DEBUG: Calculating progress for XP={xp}, Level={level}")

        current_level_xp = XPManager.xp_for_level(level)
        next_level_xp = XPManager.xp_for_level(level + 1)

        print(f"DEBUG: current_level_xp (XP needed for Level {level}) = {current_level_xp}")
        print(f"DEBUG: next_level_xp (XP needed for Level {level + 1}) = {next_level_xp}")

        xp_into_level = max(0, xp - current_level_xp)
        xp_needed = next_level_xp - current_level_xp

        print(f"DEBUG: xp_into_level (How much XP into current level) = {xp_into_level}")
        print(f"DEBUG: xp_needed (Total XP needed for next level) = {xp_needed}")

        if xp_needed <= 0:
            print("DEBUG: xp_needed <= 0, returning 100%")

            return 100

        progress = int((xp_into_level / xp_needed) * 100)
        print(f"DEBUG: Raw calculated progress = {progress}%")

        final_progress = min(progress, 100)
        print(f"DEBUG: Final progress returned = {final_progress}%")

        return final_progress

    @staticmethod
    def xp_to_next_level(xp, level):
        next_level_xp = XPManager.xp_for_level(level + 1)
        return max(0, next_level_xp - xp)


    @classmethod
    def clear_cache(cls):
        cls._cached_settings = None

    @staticmethod
    def resync_all_user_levels():
        from accounts.models import UserStats
        for stats in UserStats.objects.all():
            stats.level = XPManager.level_from_xp(stats.xp)
            stats.save(update_fields=["level"])
