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
        return int(base * (level ** exponent))

    @staticmethod
    def level_from_xp(xp):
        base, exponent = XPManager.get_settings()
        if xp <= 0:
            return 1
        return max(1, int((xp / base) ** (1 / exponent)))

    @staticmethod
    def next_level_xp(level):
        return XPManager.xp_for_level(level + 1)

    @staticmethod
    def progress_percent(xp, level):
        current_level_xp = XPManager.xp_for_level(level)
        next_level_xp = XPManager.xp_for_level(level + 1)

        xp_into_level = xp - current_level_xp
        xp_needed = next_level_xp - current_level_xp

        if xp_needed <= 0:
            return 100

        return min(int((xp_into_level / xp_needed) * 100), 100)

    @staticmethod
    def xp_to_next_level(xp, level):
        next_level_xp = XPManager.xp_for_level(level + 1)
        return max(0, next_level_xp - xp)

    @classmethod
    def clear_cache(cls):
        cls._cached_settings = None

