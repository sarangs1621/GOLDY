#!/usr/bin/env python3
"""Test dashboard data calculations directly from database"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent / 'backend'
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
db_name = os.environ.get('DB_NAME', 'gold_shop_erp')

async def test_dashboard_calculations():
    print("=" * 80)
    print("DASHBOARD DATA CALCULATIONS TEST")
    print("=" * 80)
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    # Test 1: Categories count
    print("\n[1] Testing Categories Count...")
    headers = await db.inventory_headers.find({"is_deleted": False}, {"_id": 0}).to_list(1000)
    categories_count = len(headers)
    print(f"  ✓ Total categories: {categories_count}")
    
    # Test 2: Total Stock Weight
    print("\n[2] Testing Total Stock Weight...")
    total_weight = sum(h.get('current_weight', 0) for h in headers)
    print(f"  ✓ Total stock weight: {round(total_weight, 3)}g")
    
    # Test 3: Outstanding Amount
    print("\n[3] Testing Outstanding Amount...")
    invoices = await db.invoices.find(
        {"is_deleted": False, "payment_status": {"$ne": "paid"}},
        {"_id": 0}
    ).to_list(10000)
    total_outstanding = sum(inv.get('balance_due', 0) for inv in invoices)
    print(f"  ✓ Total outstanding: {round(total_outstanding, 3)} OMR")
    print(f"  ✓ Outstanding invoices: {len(invoices)}")
    
    # Test 4: Low Stock Items
    print("\n[4] Testing Low Stock Items...")
    low_stock_count = len([h for h in headers if h.get('current_qty', 0) < 5])
    print(f"  ✓ Low stock items (qty < 5): {low_stock_count}")
    
    # Test 5: Stock Summary Table Data
    print("\n[5] Testing Stock Summary Table Data...")
    stock_data = [
        {
            "header_id": h['id'],
            "header_name": h['name'],
            "total_qty": h.get('current_qty', 0),
            "total_weight": h.get('current_weight', 0)
        }
        for h in headers
    ]
    print(f"  ✓ Stock summary rows: {len(stock_data)}")
    print(f"\n  Sample rows:")
    for item in stock_data[:5]:
        print(f"    {item['header_name']}: qty={item['total_qty']}, weight={round(item['total_weight'], 3)}g")
    
    # Summary
    print("\n" + "=" * 80)
    print("DASHBOARD METRICS SUMMARY")
    print("=" * 80)
    print(f"Categories: {categories_count}")
    print(f"Total Stock: {round(total_weight, 3)}g")
    print(f"Outstanding: {round(total_outstanding, 3)} OMR")
    print(f"Low Stock: {low_stock_count}")
    print(f"Stock Rows: {len(stock_data)}")
    
    # Check for issues
    print("\n" + "=" * 80)
    print("ISSUES DETECTED")
    print("=" * 80)
    
    issues = []
    if categories_count == 0:
        issues.append("❌ Categories count is 0 (should be 10)")
    if total_weight == 0:
        issues.append("❌ Total stock weight is 0 (should be > 0)")
    if len([row for row in stock_data if row['total_qty'] == 0 and row['total_weight'] == 0]) > 2:
        issues.append("❌ Too many rows with 0 stock")
    
    if issues:
        for issue in issues:
            print(issue)
    else:
        print("✅ No issues detected! All metrics look correct.")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(test_dashboard_calculations())
