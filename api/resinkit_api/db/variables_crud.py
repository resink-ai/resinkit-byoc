from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import update

from resinkit_api.db.models import Variable
from resinkit_api.core.encryption import encrypt_value, decrypt_value
from resinkit_api.core.logging import get_logger
from resinkit_api.utils.misc_utils import get_system_variables

logger = get_logger(__name__)


async def create_variable(db: Session, name: str, value: str, description: Optional[str] = None, created_by: str = "system") -> Variable:
    """
    Create a new variable with encrypted value.
    """
    # Encrypt the value before storing
    encrypted_value = encrypt_value(value)

    # Create the variable
    variable = Variable(name=name, encrypted_value=encrypted_value, description=description, created_by=created_by)

    db.add(variable)
    db.commit()
    db.refresh(variable)

    logger.info(f"Variable '{name}' created by {created_by}")
    return variable


async def get_variable(db: Session, name: str) -> Optional[Variable]:
    """
    Get a variable by name (without decrypting value).
    """
    return db.query(Variable).filter(Variable.name == name).first()


async def get_variable_decrypted(db: Session, name: str) -> Optional[Dict]:
    """
    Get a variable by name and decrypt its value.
    """
    variable = await get_variable(db, name)
    if not variable:
        return None

    # Return a dict with decrypted value
    return {
        "name": variable.name,
        "value": decrypt_value(variable.encrypted_value),
        "description": variable.description,
        "created_at": variable.created_at,
        "updated_at": variable.updated_at,
        "created_by": variable.created_by,
    }


async def list_variables(db: Session) -> List[Variable]:
    """
    List all variables (without decrypted values).
    """
    return db.query(Variable).all()


async def update_variable(db: Session, name: str, value: Optional[str] = None, description: Optional[str] = None) -> Optional[Variable]:
    """
    Update a variable by name.
    """
    variable = await get_variable(db, name)
    if not variable:
        return None

    # Build update data
    update_data = {}
    if value is not None:
        update_data["encrypted_value"] = encrypt_value(value)
    if description is not None:
        update_data["description"] = description

    if update_data:
        # Update the variable
        db.execute(update(Variable).where(Variable.name == name).values(**update_data))
        db.commit()
        db.refresh(variable)

    logger.info(f"Variable '{name}' updated")
    return variable


async def delete_variable(db: Session, name: str) -> bool:
    """
    Delete a variable by name.
    """
    variable = await get_variable(db, name)
    if not variable:
        return False

    db.delete(variable)
    db.commit()

    logger.info(f"Variable '{name}' deleted")
    return True


async def get_all_variables_decrypted(db: Session) -> Dict[str, str]:
    """
    Get all variables with their decrypted values as a dictionary.

    Returns:
        A dictionary mapping variable names to their decrypted values.
    """
    variables_dict = {}
    all_variables = await list_variables(db)

    for variable in all_variables:
        var_data = await get_variable_decrypted(db, variable.name)
        if var_data:
            variables_dict[variable.name] = var_data["value"]

    variables_dict.update(get_system_variables())

    logger.debug(f"Retrieved {len(variables_dict)} decrypted variables")
    return variables_dict


async def resolve_variables(db: Session, template: str) -> str:
    """
    Resolve variables in a template string.

    Variables are referenced as ${VARIABLE_NAME} in the template.
    """
    import re

    # Find all variable references
    pattern = r"\$\{([A-Za-z0-9_]+)\}"
    matches = re.findall(pattern, template)

    # Replace each variable reference with its value
    result = template
    for var_name in matches:
        variable_data = await get_variable_decrypted(db, var_name)
        if variable_data:
            # Replace ${VAR_NAME} with the decrypted value
            placeholder = f"${{{var_name}}}"
            result = result.replace(placeholder, variable_data["value"])

    return result
