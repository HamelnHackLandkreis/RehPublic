# Requirements Document

## Introduction

This document outlines the requirements for refactoring the centralized Pydantic schemas in `backend/api/schemas.py` into domain-specific schema files. The goal is to improve code organization by co-locating schemas with their respective domain modules (images, locations, spottings, statistics, user_detections, wikipedia), following the principle of domain-driven design and improving maintainability.

## Glossary

- **Schema**: A Pydantic model that defines the structure and validation rules for API request/response data
- **Domain Module**: A feature-specific directory containing related models, controllers, services, and schemas (e.g., `api/images/`, `api/locations/`)
- **Central Schemas File**: The current `backend/api/schemas.py` file containing all Pydantic schemas
- **Domain Schema File**: A new schema file within a domain module (e.g., `backend/api/images/image_schemas.py`)
- **Controller**: A FastAPI router file that defines API endpoints and uses schemas for validation
- **Shared Schema**: A schema used by multiple domain modules that should remain in a common location

## Requirements

### Requirement 1: Identify Schema Dependencies

**User Story:** As a developer, I want to understand which schemas belong to which domain modules, so that I can organize them correctly.

#### Acceptance Criteria

1. WHEN analyzing the codebase, THE System SHALL identify all schemas currently defined in `backend/api/schemas.py`
2. WHEN analyzing controller imports, THE System SHALL map each schema to the domain modules that use it
3. WHEN a schema is used by multiple domain modules, THE System SHALL classify it as a shared schema
4. THE System SHALL document the mapping of schemas to domain modules in the design document

### Requirement 2: Create Domain-Specific Schema Files

**User Story:** As a developer, I want schemas organized within their respective domain modules, so that related code is co-located and easier to maintain.

#### Acceptance Criteria

1. THE System SHALL create a schema file named `{domain}_schemas.py` within each domain module directory
2. WHEN creating schema files, THE System SHALL follow the naming pattern: `api/images/image_schemas.py`, `api/locations/location_schemas.py`, etc.
3. THE System SHALL move domain-specific schemas from `backend/api/schemas.py` to their respective domain schema files
4. THE System SHALL preserve all schema definitions, including docstrings, field definitions, and validation rules
5. THE System SHALL maintain the ReST docstring format as specified in the Python steering rules

### Requirement 3: Handle Shared Schemas

**User Story:** As a developer, I want shared schemas to remain accessible to all modules, so that I don't create circular dependencies.

#### Acceptance Criteria

1. WHEN a schema is used by multiple domain modules, THE System SHALL keep it in `backend/api/schemas.py`
2. THE System SHALL document which schemas remain shared and the rationale for keeping them centralized
3. THE System SHALL ensure shared schemas include common response models like `BoundingBoxResponse` and `DetectionResponse`

### Requirement 4: Update Import Statements

**User Story:** As a developer, I want all import statements updated correctly, so that the application continues to function without errors.

#### Acceptance Criteria

1. THE System SHALL update all controller files to import schemas from their new domain-specific locations
2. THE System SHALL update any service files that import schemas to use the new import paths
3. THE System SHALL update test files to import schemas from their new locations
4. WHEN a module imports multiple schemas, THE System SHALL group imports by source module following Python import conventions
5. THE System SHALL maintain alphabetical ordering of imports within each group

### Requirement 5: Maintain Backward Compatibility

**User Story:** As a developer, I want the API to continue functioning identically after the refactoring, so that no existing functionality is broken.

#### Acceptance Criteria

1. THE System SHALL ensure all API endpoints continue to use the same request and response schemas
2. THE System SHALL verify that schema validation rules remain unchanged
3. THE System SHALL ensure that Pydantic model configurations (e.g., `model_config`) are preserved
4. THE System SHALL maintain all schema relationships and nested models

### Requirement 6: Validate the Refactoring

**User Story:** As a developer, I want to verify that the refactoring is successful, so that I can be confident the code works correctly.

#### Acceptance Criteria

1. THE System SHALL run type checking using mypy to verify no type errors exist
2. THE System SHALL verify that all import statements resolve correctly
3. THE System SHALL check that no circular import dependencies are created
4. THE System SHALL ensure the FastAPI application starts successfully
5. THE System SHALL verify that the OpenAPI documentation generates correctly at `/docs`
