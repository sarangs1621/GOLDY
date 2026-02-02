#!/usr/bin/env python3
"""
Purchase Formula Sanity Test

Tests the CORRECT formula: amount = ((weight × (purity/916)) ÷ conversion_factor) × rate

SANITY TEST (NON-NEGOTIABLE):
If purity = 916 and rate = 1 → amount MUST equal (weight ÷ conversion_factor)
"""

def calculate_purchase_amount(weight, purity, conversion_factor, rate):
    """
    CORRECT FORMULA (LOCKED):
    1. Normalize purity to 22K (916)
    2. Adjust weight to 22K equivalent  
    3. Apply conversion factor
    4. Apply rate per gram
    """
    purity_ratio = purity / 916.0
    adjusted_weight = weight * purity_ratio
    converted_weight = adjusted_weight / conversion_factor
    amount = converted_weight * rate
    return round(amount, 3)


def test_sanity_check():
    """
    SANITY TEST: If purity = 916 and rate = 1 → amount MUST equal (weight ÷ conversion_factor)
    """
    print("=" * 80)
    print("SANITY TEST (NON-NEGOTIABLE)")
    print("=" * 80)
    
    weight = 5.0
    purity = 916
    rate = 1.0
    conversion_factor = 0.920
    
    expected = weight / conversion_factor
    actual = calculate_purchase_amount(weight, purity, conversion_factor, rate)
    
    print(f"\nTest Parameters:")
    print(f"  Weight: {weight} g")
    print(f"  Purity: {purity}")
    print(f"  Rate: {rate} OMR/g")
    print(f"  Conversion Factor: {conversion_factor}")
    
    print(f"\nExpected Result: {weight} ÷ {conversion_factor} = {expected:.3f} OMR")
    print(f"Actual Result: {actual:.3f} OMR")
    
    if abs(actual - expected) < 0.001:
        print("\n✅ PASS: Formula is correct!")
        return True
    else:
        print(f"\n❌ FAIL: Formula is WRONG! Difference: {abs(actual - expected):.3f}")
        return False


def test_different_purities():
    """
    Test with different purities to verify the formula behavior
    """
    print("\n" + "=" * 80)
    print("COMPREHENSIVE PURITY TESTS")
    print("=" * 80)
    
    weight = 5.0
    rate = 1.0
    conversion_factor = 0.920
    
    test_cases = [
        (916, "22K (baseline)", 1.0),
        (999, "24K (higher purity)", 999/916),
        (875, "21K (lower purity)", 875/916),
        (750, "18K", 750/916),
    ]
    
    all_pass = True
    
    for purity, description, expected_multiplier in test_cases:
        amount = calculate_purchase_amount(weight, purity, conversion_factor, rate)
        
        # Calculate what we expect step by step
        purity_ratio = purity / 916.0
        adjusted_weight = weight * purity_ratio
        converted_weight = adjusted_weight / conversion_factor
        expected_amount = converted_weight * rate
        
        print(f"\n{description} (Purity: {purity}):")
        print(f"  Step 1 - Purity Ratio: {purity}/916 = {purity_ratio:.4f}")
        print(f"  Step 2 - Adjusted Weight: {weight}g × {purity_ratio:.4f} = {adjusted_weight:.3f}g")
        print(f"  Step 3 - Converted Weight: {adjusted_weight:.3f}g ÷ {conversion_factor} = {converted_weight:.3f}g")
        print(f"  Step 4 - Amount: {converted_weight:.3f}g × {rate} OMR/g = {amount:.3f} OMR")
        
        # Verify calculation
        if abs(amount - expected_amount) < 0.001:
            print(f"  ✅ Calculation verified")
        else:
            print(f"  ❌ Calculation FAILED")
            all_pass = False
    
    return all_pass


def test_real_world_scenario():
    """
    Test with real-world scenario from user's example
    """
    print("\n" + "=" * 80)
    print("REAL-WORLD SCENARIO TEST")
    print("=" * 80)
    
    weight = 5.0
    purity = 916
    rate = 1.0
    conversion_factor = 0.920
    
    amount = calculate_purchase_amount(weight, purity, conversion_factor, rate)
    
    print(f"\nScenario: Purchase 5g of 22K gold at 1 OMR/g with factor 0.920")
    print(f"\nStep-by-step calculation:")
    print(f"  1. Purity Ratio: {purity}/916 = {purity/916:.4f}")
    print(f"  2. Adjusted Weight: {weight}g × {purity/916:.4f} = {weight * purity/916:.3f}g")
    print(f"  3. Converted Weight: {weight * purity/916:.3f}g ÷ {conversion_factor} = {weight * purity/916 / conversion_factor:.3f}g")
    print(f"  4. Final Amount: {weight * purity/916 / conversion_factor:.3f}g × {rate} = {amount:.3f} OMR")
    
    print(f"\nExpected: ~5.435 OMR")
    print(f"Actual: {amount:.3f} OMR")
    
    if abs(amount - 5.435) < 0.001:
        print("✅ CORRECT: Result matches expected value!")
        return True
    else:
        print("❌ WRONG: Result does NOT match expected value!")
        return False


if __name__ == "__main__":
    print("\n🧪 PURCHASE FORMULA VALIDATION TEST")
    print("Testing CORRECT formula: amount = ((weight × (purity/916)) ÷ conversion_factor) × rate\n")
    
    results = []
    
    # Run all tests
    results.append(("Sanity Check", test_sanity_check()))
    results.append(("Different Purities", test_different_purities()))
    results.append(("Real-World Scenario", test_real_world_scenario()))
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    all_passed = all(passed for _, passed in results)
    
    if all_passed:
        print("\n🎉 ALL TESTS PASSED - Formula is CORRECT!")
        exit(0)
    else:
        print("\n❌ SOME TESTS FAILED - Formula is WRONG!")
        exit(1)
