from howlongtobeatpy import HowLongToBeat
from gaming.models import Game

def fetch_hltb_data(title):
    try:
        results = HowLongToBeat().search(title)
        if not results:
            print(f"🔍 No HLTB results found for '{title}'")
            return None

        best_match = max(results, key=lambda r: r.similarity)
        print(f"✅ HLTB best match: {best_match.game_name} ({best_match.similarity*100:.1f}% match)")

        return {
            "title": best_match.game_name,
            "hours_main_story": round(best_match.main_story or 0),
            "hours_main_extra": round(best_match.main_extra or 0),
            "hours_completionist": round(best_match.completionist or 0),
        }

    except Exception as e:
        print("❌ HLTB fetch error:", e)
        return None