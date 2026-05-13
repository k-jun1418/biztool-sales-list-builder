from places_api import search_places
from csv_export import export_csv


def main():
    print("=== BizTool Sales List Builder ===")

    area = input("地域を入力してください（例：埼玉県 川口市）: ").strip()
    business_type = input("業種を入力してください（例：不動産会社）: ").strip()

    if not area or not business_type:
        print("地域と業種は必須です。")
        return

    print("\n検索中...")
    rows = search_places(
        area=area,
        business_type=business_type,
        max_pages=1,
    )

    print(f"取得件数: {len(rows)} 件")

    if not rows:
        print("データが取得できませんでした。")
        return

    filepath = export_csv(rows, area, business_type)
    print(f"CSV出力完了: {filepath}")


if __name__ == "__main__":
    main()