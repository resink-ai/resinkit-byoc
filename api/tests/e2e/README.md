# Quick start

```bash
./scripts/e2e.sh test_delete_paimon_catalog paimon_catalog_name=test_jdbc_catalog_create_xyz
./scripts/e2e.sh list catalogstore
```

# How to add a new e2e test

1. Create a new test file in the api/tests/e2e/ directory following the pattern of existing files
2. Extend the E2eBase class which provides common testing utilities
3. Implement test methods with descriptive names (prefixed with test\_)
4. Use the base class methods for HTTP operations (get, post, put, delete)
5. Use assertion utilities like assert_status_code and assert_json_response
6. Add setup/teardown methods if needed
