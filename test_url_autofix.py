"""
Test URL auto-fix logic for link attachments.
This script tests the URL transformation logic used in document_tracking/views.py
"""

def auto_fix_url(url):
    """
    Auto-fix URL format (same logic as in submit_document view).
    """
    url_clean = url.strip()
    
    if not url_clean:
        return None
    
    # 1. Add protocol if missing
    if not url_clean.startswith(('http://', 'https://', 'ftp://')):
        url_clean = 'https://' + url_clean
        print(f"  Added protocol: {url_clean}")
    
    # 2. Add .com if no domain extension
    url_without_protocol = url_clean.replace('https://', '').replace('http://', '').replace('ftp://', '')
    domain_part = url_without_protocol.split('/')[0].split('?')[0]
    
    if '.' not in domain_part and ':' not in domain_part:  # No TLD and not localhost:port
        # Insert .com before any path or query
        if '/' in url_without_protocol:
            parts = url_without_protocol.split('/', 1)
            url_clean = url_clean.replace(url_without_protocol, parts[0] + '.com/' + parts[1])
        elif '?' in url_without_protocol:
            parts = url_without_protocol.split('?', 1)
            url_clean = url_clean.replace(url_without_protocol, parts[0] + '.com?' + parts[1])
        else:
            url_clean = url_clean + '.com'
        print(f"  Added .com: {url_clean}")
    
    return url_clean


def test_url_autofix():
    """Test various URL formats."""
    test_cases = [
        # (input, expected_output)
        ("aynata", "https://aynata.com"),
        ("google.com", "https://google.com"),
        ("example.com/page", "https://example.com/page"),
        ("github.com/user/repo", "https://github.com/user/repo"),
        ("https://example.com", "https://example.com"),
        ("http://example.com", "http://example.com"),
        ("example", "https://example.com"),
        ("example/path", "https://example.com/path"),
        ("example?query=1", "https://example.com?query=1"),
        ("subdomain.example.com", "https://subdomain.example.com"),
        ("example.com:8080", "https://example.com:8080"),
        ("localhost:3000", "https://localhost:3000"),
        ("", None),
        ("   ", None),
    ]
    
    print("=" * 60)
    print("URL AUTO-FIX TEST")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for input_url, expected in test_cases:
        print(f"\nInput: '{input_url}'")
        result = auto_fix_url(input_url)
        print(f"Result: {result}")
        print(f"Expected: {expected}")
        
        if result == expected:
            print("✓ PASS")
            passed += 1
        else:
            print("✗ FAIL")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)


if __name__ == "__main__":
    test_url_autofix()
