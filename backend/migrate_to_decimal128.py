#!/usr/bin/env python3
"""
Decimal128 Migration Script for Gold Shop ERP
==============================================
This script converts all existing float values in the database to Decimal128
for precise financial and weight calculations (3 decimal precision).

IMPORTANT: Run this script ONCE after deploying the Decimal128 conversion code.

Usage:
    python migrate_to_decimal128.py [--dry-run] [--collection COLLECTION_NAME]
    
Options:
    --dry-run           Show what would be migrated without making changes
    --collection NAME   Only migrate specific collection (e.g., 'invoices')
    
Examples:
    python migrate_to_decimal128.py --dry-run
    python migrate_to_decimal128.py --collection invoices
    python migrate_to_decimal128.py  # Migrate all collections
"""

import asyncio
import os
import sys
from datetime import datetime, timezone
from decimal import Decimal
from motor.motor_asyncio import AsyncIOMotorClient
from bson.decimal128 import Decimal128

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import conversion utilities from server.py
from server import (
    convert_invoice_to_decimal,
    convert_purchase_to_decimal,
    convert_transaction_to_decimal,
    convert_account_to_decimal,
    convert_stock_movement_to_decimal,
    convert_gold_ledger_to_decimal,
    convert_daily_closing_to_decimal,
    convert_return_to_decimal,
    _safe_decimal128
)

# MongoDB connection
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017/gold_shop")
client = AsyncIOMotorClient(MONGO_URL)
db = client.get_database()

async def migrate_collection(collection_name, converter_func, dry_run=False):
    """
    Migrate a single collection using the provided converter function.
    
    Args:
        collection_name: Name of the collection to migrate
        converter_func: Function to convert document data
        dry_run: If True, only show what would be changed
    
    Returns:
        (migrated_count, error_count)
    """
    collection = db[collection_name]
    
    print(f"\n{'[DRY RUN] ' if dry_run else ''}Migrating collection: {collection_name}")
    print("=" * 80)
    
    # Get all documents
    cursor = collection.find({})
    documents = await cursor.to_list(length=None)
    total = len(documents)
    
    if total == 0:
        print(f"  No documents found in {collection_name}")
        return 0, 0
    
    print(f"  Found {total} documents")
    
    migrated_count = 0
    error_count = 0
    
    for doc in documents:
        try:
            # Skip _id field
            doc_id = doc['_id']
            
            # Convert the document
            converted = converter_func(doc)
            
            # Check if any changes were made
            has_changes = False
            for key, value in converted.items():
                if key != '_id' and isinstance(value, Decimal128):
                    original_value = doc.get(key)
                    if not isinstance(original_value, Decimal128):
                        has_changes = True
                        break
            
            if has_changes:
                if not dry_run:
                    # Update the document
                    await collection.update_one(
                        {"_id": doc_id},
                        {"$set": converted}
                    )
                migrated_count += 1
                
                if migrated_count <= 3:  # Show first 3 examples
                    print(f"  ✓ Migrated document ID: {doc.get('id', 'N/A')}")
        
        except Exception as e:
            error_count += 1
            print(f"  ✗ Error migrating document ID {doc.get('id', 'N/A')}: {str(e)}")
    
    print(f"\n  Results:")
    print(f"    - Total documents: {total}")
    print(f"    - Migrated: {migrated_count}")
    print(f"    - Errors: {error_count}")
    print(f"    - Unchanged: {total - migrated_count - error_count}")
    
    return migrated_count, error_count

async def migrate_parties(dry_run=False):
    """
    Migrate party balance fields (if they exist in future).
    Currently parties don't have balance fields, but this is a placeholder.
    """
    collection_name = "parties"
    collection = db[collection_name]
    
    print(f"\n{'[DRY RUN] ' if dry_run else ''}Migrating collection: {collection_name}")
    print("=" * 80)
    
    cursor = collection.find({})
    documents = await cursor.to_list(length=None)
    total = len(documents)
    
    print(f"  Found {total} documents (no balance fields to migrate)")
    return 0, 0

async def migrate_all(dry_run=False, specific_collection=None):
    """
    Migrate all collections with float data to Decimal128.
    
    Args:
        dry_run: If True, only show what would be changed
        specific_collection: If provided, only migrate this collection
    """
    print("\n" + "=" * 80)
    print(f"  Decimal128 Migration Script - Gold Shop ERP")
    print(f"  {'DRY RUN MODE - No changes will be made' if dry_run else 'PRODUCTION MODE - Data will be updated'}")
    print(f"  Started at: {datetime.now(timezone.utc).isoformat()}")
    print("=" * 80)
    
    # Define collection migration tasks
    migration_tasks = [
        ("invoices", convert_invoice_to_decimal),
        ("purchases", convert_purchase_to_decimal),
        ("transactions", convert_transaction_to_decimal),
        ("accounts", convert_account_to_decimal),
        ("stock_movements", convert_stock_movement_to_decimal),
        ("gold_ledger", convert_gold_ledger_to_decimal),
        ("daily_closings", convert_daily_closing_to_decimal),
        ("returns", convert_return_to_decimal),
    ]
    
    # Filter for specific collection if requested
    if specific_collection:
        migration_tasks = [task for task in migration_tasks if task[0] == specific_collection]
        if not migration_tasks:
            print(f"\n✗ Collection '{specific_collection}' not found in migration list")
            return
    
    total_migrated = 0
    total_errors = 0
    
    # Migrate each collection
    for collection_name, converter_func in migration_tasks:
        migrated, errors = await migrate_collection(collection_name, converter_func, dry_run)
        total_migrated += migrated
        total_errors += errors
    
    # Migrate parties (placeholder)
    if not specific_collection or specific_collection == "parties":
        migrated, errors = await migrate_parties(dry_run)
        total_migrated += migrated
        total_errors += errors
    
    # Final summary
    print("\n" + "=" * 80)
    print("  MIGRATION SUMMARY")
    print("=" * 80)
    print(f"  Total migrated: {total_migrated}")
    print(f"  Total errors: {total_errors}")
    print(f"  Completed at: {datetime.now(timezone.utc).isoformat()}")
    
    if dry_run:
        print("\n  ℹ️  This was a DRY RUN. No changes were made to the database.")
        print("  Run without --dry-run to apply changes.")
    else:
        print("\n  ✓ Migration completed successfully!")
    
    print("=" * 80)

async def main():
    """Main entry point for the migration script."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Migrate Gold Shop ERP data to Decimal128')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be migrated without making changes')
    parser.add_argument('--collection', type=str, help='Only migrate specific collection')
    
    args = parser.parse_args()
    
    try:
        await migrate_all(dry_run=args.dry_run, specific_collection=args.collection)
    except Exception as e:
        print(f"\n✗ Migration failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(main())
