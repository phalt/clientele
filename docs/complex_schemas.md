# 🔀 Complex Schemas

Clientele fully supports OpenAPI's complex schema combinations including `oneOf`, `anyOf`, and `nullable` fields. This ensures proper type discrimination and null handling in your generated clients.

## oneOf - Discriminated Unions

The `oneOf` keyword indicates that a value must match exactly one of several schemas. This is useful for modeling polymorphic types where you know the exact type at runtime.

### Schema Example

```json
{
  "components": {
    "schemas": {
      "Cat": {
        "type": "object",
        "properties": {
          "type": { "type": "string", "enum": ["cat"] },
          "meow_volume": { "type": "integer" }
        }
      },
      "Dog": {
        "type": "object",
        "properties": {
          "type": { "type": "string", "enum": ["dog"] },
          "bark_volume": { "type": "integer" }
        }
      },
      "PetRequest": {
        "oneOf": [
          { "$ref": "#/components/schemas/Cat" },
          { "$ref": "#/components/schemas/Dog" }
        ],
        "discriminator": {
          "propertyName": "type"
        }
      }
    }
  }
}
```

### Generated Code

Clientele generates a type alias for `oneOf` schemas using `typing.Union`:

```python
class Cat(pydantic.BaseModel):
    type_: str
    meow_volume: int

class Dog(pydantic.BaseModel):
    type_: str
    bark_volume: int

# Type alias for the union (using typing.Union for forward references)
PetRequest = typing.Union[Cat, Dog]
```

### Usage

You can use the generated type alias with proper type checking:

```python
from my_client import client, schemas

# Create a cat
cat = schemas.Cat(type_="cat", meow_volume=10)
response = client.create_pet(data=cat)

# Create a dog
dog = schemas.Dog(type_="dog", bark_volume=15)
response = client.create_pet(data=dog)

# Pattern matching for handling the response
match response:
    case schemas.Cat():
        print(f"Cat meows at volume {response.meow_volume}")
    case schemas.Dog():
        print(f"Dog barks at volume {response.bark_volume}")
```

## anyOf - Flexible Unions

The `anyOf` keyword indicates that a value can match one or more of the specified schemas. This is useful when you need flexibility in the types accepted.

### Schema Example

```json
{
  "components": {
    "schemas": {
      "FlexibleIdResponse": {
        "type": "object",
        "properties": {
          "id": {
            "anyOf": [
              { "type": "string" },
              { "type": "integer" }
            ]
          },
          "data": { "type": "string" }
        }
      }
    }
  }
}
```

### Generated Code

Clientele generates union types for `anyOf` schemas:

```python
class FlexibleIdResponse(pydantic.BaseModel):
    id: str | int
    data: str
```

### Usage

The generated types work seamlessly with Pydantic's validation:

```python
from my_client import client, schemas

# Both string and integer IDs are valid
response1 = schemas.FlexibleIdResponse(id="abc123", data="test")
response2 = schemas.FlexibleIdResponse(id=12345, data="test")

# Pydantic handles validation automatically
response = client.get_flexible_data()
if isinstance(response.id, str):
    print(f"String ID: {response.id}")
elif isinstance(response.id, int):
    print(f"Integer ID: {response.id}")
```

## nullable - Optional Values

The `nullable` keyword indicates that a field can be `null` in addition to its defined type. Clientele converts nullable fields to proper Python `Optional` types.

### Schema Example

```json
{
  "components": {
    "schemas": {
      "NullableFieldsResponse": {
        "type": "object",
        "properties": {
          "required_field": { "type": "string" },
          "optional_nullable_field": {
            "type": "string",
            "nullable": true
          },
          "nullable_number": {
            "type": "integer",
            "nullable": true
          }
        },
        "required": ["required_field"]
      }
    }
  }
}
```

### Generated Code

Clientele generates `Optional` types for nullable fields:

```python
class NullableFieldsResponse(pydantic.BaseModel):
    required_field: str
    optional_nullable_field: typing.Optional[str]
    nullable_number: typing.Optional[int]
```

### Usage

Nullable fields work naturally with Python's type system:

```python
from my_client import client, schemas

# All of these are valid
response1 = schemas.NullableFieldsResponse(
    required_field="test",
    optional_nullable_field="value",
    nullable_number=42
)

response2 = schemas.NullableFieldsResponse(
    required_field="test",
    optional_nullable_field=None,  # Explicitly null
    nullable_number=None
)

response3 = schemas.NullableFieldsResponse(
    required_field="test"  # Optional fields can be omitted
)

# Check for null values
response = client.get_data()
if response.optional_nullable_field is not None:
    print(f"Value: {response.optional_nullable_field}")
else:
    print("Field is null")
```

## Complex Combinations

You can combine `oneOf`, `anyOf`, and `nullable` for even more expressive schemas:

### Schema Example

```json
{
  "properties": {
    "payment_method": {
      "oneOf": [
        { "$ref": "#/components/schemas/CreditCard" },
        { "$ref": "#/components/schemas/BankTransfer" },
        { "$ref": "#/components/schemas/PayPal" }
      ],
      "nullable": true
    }
  }
}
```

### Generated Code

```python
# Type alias with optional wrapper (using typing.Union for forward refs)
PaymentMethod = typing.Optional[typing.Union[CreditCard, BankTransfer, PayPal]]
```

## Python Version Compatibility

Clientele generates code compatible with your Python version:

- **Python 3.10+**: Uses modern union syntax (`str | int`) for inline types
- **Forward references**: Always uses `typing.Union` (e.g., `typing.Union["Cat", "Dog"]`) because the `|` operator doesn't work with string literals

The generated code automatically adapts to your target Python version for maximum compatibility.

## Testing with Complex Schemas

Complex schemas work beautifully with pattern matching and type checking:

```python
from my_client import client, schemas

def handle_pet(pet: schemas.Cat | schemas.Dog) -> str:
    match pet:
        case schemas.Cat(meow_volume=vol):
            return f"Cat meows at volume {vol}"
        case schemas.Dog(bark_volume=vol):
            return f"Dog barks at volume {vol}"

# Your IDE will provide full autocomplete and type checking
response = client.get_pet()
message = handle_pet(response)
```

## Why This Matters

Proper support for `oneOf`, `anyOf`, and `nullable` ensures:

1. **Type Safety**: Your IDE and type checkers understand exactly what types are valid
2. **Better Developer Experience**: Autocomplete works correctly for union types
3. **Runtime Validation**: Pydantic validates that values match the schema
4. **Clear Code**: Type aliases make complex schemas easy to understand
5. **Pattern Matching**: Python 3.10+ pattern matching works seamlessly

This puts Clientele on par with (or ahead of) commercial alternatives like Speakeasy, while maintaining our commitment to clean, readable, Pythonic code.
