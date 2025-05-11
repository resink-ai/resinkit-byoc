# Quick start

```bash
./scripts/e2e.sh test_delete_paimon_catalog paimon_catalog_name=test_jdbc_catalog_create_xyz
./scripts/e2e.sh list catalogstore
```

# How to add a new e2e test

- Create a new test file in the api/tests/e2e/ directory following the pattern of existing files
- Extend the E2eBase class which provides common testing utilities
- Implement test methods with descriptive names (prefixed with test\_)
- Use the base class methods for HTTP operations (get, post, put, delete)
- Use assertion utilities like assert_status_code and assert_json_response
- Add setup/teardown methods if needed

