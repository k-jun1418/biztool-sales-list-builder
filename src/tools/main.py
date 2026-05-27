from sales_list_builder.places_api import search_places
from sales_list_builder.csv_export import export_csv
from sales_list_builder.config_loader import load_config
from sales_list_builder.contact_lead_enricher import enrich_leads

def main():

    print("=== BizTool Sales List Builder ===")

    area = input("地域を入力してください（例：埼玉県 川口市）: ").strip()
    business_type = input("業種を入力してください（例：不動産会社）: ").strip()

    max_results = input("取得件数（20 / 40 / 60）: ").strip()

    try:
        max_results = int(max_results)
    except ValueError:
        max_results = 20

    # 最小20、最大60
    max_results = max(20, min(max_results, 60))

    # Places APIは1ページ20件
    max_pages = max_results // 20

    if not area or not business_type:
        print("地域と業種は必須です。")
        return

    print("\n検索中...")
    config = load_config()

    max_pages = config.get("max_pages", 1)

    result = search_places(
        area=area,
        business_type=business_type,
        max_pages=max_pages,
    )

    rows = result["rows"]
    total_count = result["total_count"]

    print(f"\n{total_count}件取得しました。")

    if not rows:
        print("データが取得できませんでした。")
        return

    print("メール・問い合わせ情報を取得中...")

    rows = enrich_leads(rows)

    filepath = export_csv(rows, area, business_type)

    print(f"CSV出力完了: {filepath}")


if __name__ == "__main__":
    main()