import pytest
from sqlalchemy.orm import Session
from resinkit_api.db.models import Variable
from resinkit_api.db import variables_crud
from resinkit_api.core.encryption import encrypt_value, decrypt_value


# Test encryption/decryption
def test_encryption():
    original_value = "this is a secret"
    encrypted = encrypt_value(original_value)
    
    # Encrypted value should be different from original
    assert encrypted != original_value
    
    # Decryption should yield the original value
    decrypted = decrypt_value(encrypted)
    assert decrypted == original_value


# Test variable CRUD operations
@pytest.mark.asyncio
async def test_variable_crud(db: Session):
    # Test variable creation
    test_var_name = "TEST_VAR"
    test_var_value = "test value"
    test_var_desc = "A test variable"
    
    var = await variables_crud.create_variable(
        db=db,
        name=test_var_name,
        value=test_var_value,
        description=test_var_desc,
        created_by="test"
    )
    
    assert var.name == test_var_name
    assert var.description == test_var_desc
    # Value should be encrypted
    assert var.encrypted_value != test_var_value
    
    # Test variable retrieval with decryption
    var_decrypted = await variables_crud.get_variable_decrypted(db, test_var_name)
    assert var_decrypted["name"] == test_var_name
    assert var_decrypted["value"] == test_var_value
    
    # Test variable update
    new_value = "updated value"
    updated_var = await variables_crud.update_variable(
        db=db,
        name=test_var_name,
        value=new_value
    )
    
    var_decrypted = await variables_crud.get_variable_decrypted(db, test_var_name)
    assert var_decrypted["value"] == new_value
    
    # Test variable deletion
    result = await variables_crud.delete_variable(db, test_var_name)
    assert result is True
    
    # Variable should no longer exist
    var = await variables_crud.get_variable(db, test_var_name)
    assert var is None


# Test variable resolution in templates
@pytest.mark.asyncio
async def test_variable_resolution(db: Session):
    # Create test variables
    await variables_crud.create_variable(
        db=db, 
        name="HOSTNAME", 
        value="example.com", 
        created_by="test"
    )
    
    await variables_crud.create_variable(
        db=db, 
        name="DB_PASSWORD", 
        value="secret123", 
        created_by="test"
    )
    
    # Test simple variable replacement
    template = "The hostname is ${HOSTNAME}"
    resolved = await variables_crud.resolve_variables(db, template)
    assert resolved == "The hostname is example.com"
    
    # Test multiple variables
    template = """
    hostname: ${HOSTNAME}
    password: ${DB_PASSWORD}
    """
    resolved = await variables_crud.resolve_variables(db, template)
    assert "hostname: example.com" in resolved
    assert "password: secret123" in resolved
    
    # Test with nonexistent variable (should remain unchanged)
    template = "Unknown variable: ${NONEXISTENT}"
    resolved = await variables_crud.resolve_variables(db, template)
    assert resolved == "Unknown variable: ${NONEXISTENT}"
    
    # Clean up
    await variables_crud.delete_variable(db, "HOSTNAME")
    await variables_crud.delete_variable(db, "DB_PASSWORD") 