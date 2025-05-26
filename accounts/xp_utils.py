from accounts.models import XPTable, ChoreXPTable, ReadingXPTable, GamingXPTable


class XPManager:
    TABLE_MAP = {
        "overall": {
            "model": XPTable,
            "level_field": "overall_level",
            "xp_field": "xp_required"
        },
        "chore": {
            "model": ChoreXPTable,
            "level_field": "chore_level",
            "xp_field": "chore_xp_required"
        },
        "reading": {
            "model": ReadingXPTable,
            "level_field": "reading_level",
            "xp_field": "reading_xp_required"
        },
        "gaming": {
            "model": GamingXPTable,
            "level_field": "gaming_level",
            "xp_field": "gaming_xp_required"
        },
    }

    @classmethod
    def level_info(cls, xp: int, kind="overall") -> dict:
        """Return level info dict for a given XP value and leveling kind."""
        config = cls.TABLE_MAP.get(kind)
        if not config:
            raise ValueError(f"Unknown XP kind: {kind}")

        model = config["model"]
        level_field = config["level_field"]
        xp_field = config["xp_field"]

        current_entry = (
            model.objects
            .filter(**{f"{xp_field}__lte": xp})
            .order_by(f"-{level_field}")
            .first()
        )

        level = getattr(current_entry, level_field, 1) if current_entry else 1
        current_xp = getattr(current_entry, xp_field, 0) if current_entry else 0

        next_entry = model.objects.filter(**{level_field: level + 1}).first()
        next_xp = getattr(next_entry, xp_field, current_xp) if next_entry else current_xp

        progress_percent = (
            100 if next_xp == current_xp
            else round((xp - current_xp) / (next_xp - current_xp) * 100, 2)
        )

        return {
            "level": level,
            "current_xp": current_xp,
            "next_xp": next_xp,
            "progress_percent": progress_percent,
            "xp_to_next": max(0, next_xp - xp),
        }

    @classmethod
    def clear_cache(cls):
        """Stub to match interface; implement caching logic if used later."""
        # No internal cache used yet, but this keeps the interface consistent.
        pass

    @classmethod
    def resync_all_user_levels(cls):
        """Recalculate and persist levels for all users."""
        from accounts.models import UserStats

        for stats in UserStats.objects.all():
            stats.update_levels()
