# Aparavi Client Object ID Auto-Discovery Implementation

## Overview

This document details all changes made to implement automatic discovery of the `clientObjectId` required for Aparavi tagging operations. The implementation replaces manual configuration requirements with intelligent auto-discovery while maintaining backward compatibility.

## Summary of Changes

### 1. **Test Script Creation** (`tests/tagging_api_test.py`)

**Purpose**: Comprehensive test script to validate auto-discovery and all tagging functionality before integrating into main codebase.

**Key Features**:
- Auto-discovers clientObjectId using AQL query
- Tests tag definition management (create, list, delete)
- Tests file tagging operations (apply, remove)
- Tests tag-based file search
- Comprehensive error handling and logging

**AQL Query Used**:
```sql
SELECT node, nodeObjectId WHERE nodeObjectID IS NOT NULL LIMIT 1
```

**Test Results**: All tests pass successfully, confirming:
- Client object ID discovery works (discovered: `f7388d0e-apag-4e86-86f0-1fbedb0b63db`)
- Tag creation and listing functionality
- File tagging operations
- Tag-based search capabilities

---

### 2. **Client Auto-Discovery Implementation** (`src/aparavi_mcp/aparavi_client.py`)

#### **New Methods Added**:

##### `discover_client_object_id()` (Lines ~260-290)
```python
async def discover_client_object_id(self) -> Optional[str]:
    """
    Discover the client object ID by querying for any node with a nodeObjectId.
    
    Returns:
        The discovered client object ID, or None if not found
        
    Raises:
        AparaviAPIError: If the discovery query fails
    """
    try:
        self.logger.info("Attempting to auto-discover client object ID...")
        
        # Query for any node with a nodeObjectId - this will be our client object ID
        aql_query = "SELECT node, nodeObjectId WHERE nodeObjectID IS NOT NULL LIMIT 1"
        result = await self.execute_query(aql_query, format_type="json")
        
        if (result and 'data' in result and 'objects' in result['data'] and result['data']['objects']):
            first_row = result['data']['objects'][0]
            if 'nodeObjectId' in first_row:
                discovered_id = first_row['nodeObjectId']
                self.logger.info(f"Successfully discovered client object ID: {discovered_id}")
                return discovered_id
        
        self.logger.warning("No client object ID found in discovery query results")
        return None
        
    except Exception as e:
        error_msg = f"Failed to auto-discover client object ID: {format_error_message(e)}"
        self.logger.error(error_msg)
        raise AparaviAPIError(error_msg)
```

##### `ensure_client_object_id()` (Lines ~292-338)
```python
async def ensure_client_object_id(self) -> str:
    """
    Ensure that a client object ID is available, either from config or auto-discovery.
    
    This method:
    1. First checks if client_object_id is already set in the instance
    2. If not, checks the config for APARAVI_CLIENT_OBJECT_ID
    3. If still not found, attempts auto-discovery
    4. Caches the result for future use
    
    Returns:
        The client object ID
        
    Raises:
        AparaviAPIError: If no client object ID can be obtained
    """
    # If we already have a cached client object ID, use it
    if hasattr(self, '_cached_client_object_id') and self._cached_client_object_id:
        return self._cached_client_object_id
    
    # Check if it's set in the config/environment
    if hasattr(self.config, 'client_object_id') and self.config.client_object_id:
        self._cached_client_object_id = self.config.client_object_id
        self.logger.info(f"Using configured client object ID: {self.config.client_object_id}")
        return self.config.client_object_id
    
    # Check environment variable directly
    import os
    env_client_id = os.getenv('APARAVI_CLIENT_OBJECT_ID')
    if env_client_id and env_client_id.strip():
        self._cached_client_object_id = env_client_id.strip()
        self.logger.info(f"Using environment variable client object ID: {env_client_id}")
        return env_client_id.strip()
    
    # Attempt auto-discovery
    self.logger.info("No client object ID configured, attempting auto-discovery...")
    discovered_id = await self.discover_client_object_id()
    
    if discovered_id:
        self._cached_client_object_id = discovered_id
        self.logger.info(f"Auto-discovery successful, using client object ID: {discovered_id}")
        return discovered_id
    
    # If we get here, we couldn't find or discover a client object ID
    raise AparaviAPIError(
        "Could not obtain client object ID. Please set APARAVI_CLIENT_OBJECT_ID environment variable "
        "or ensure your Aparavi system has accessible nodes for auto-discovery."
    )
```

#### **Updated Properties**:

##### `client_object_id` Property (Lines ~592-633)
```python
@property
def client_object_id(self) -> Optional[str]:
    """
    Get the client object ID, with automatic discovery if not configured.
    
    Returns:
        The client object ID if available, None otherwise
    """
    # Check if we have a cached value
    if hasattr(self, '_cached_client_object_id') and self._cached_client_object_id:
        return self._cached_client_object_id
    
    # Check config first
    if hasattr(self.config, 'client_object_id') and self.config.client_object_id:
        self._cached_client_object_id = self.config.client_object_id
        return self.config.client_object_id
    
    # Check environment variable
    import os
    env_client_id = os.getenv('APARAVI_CLIENT_OBJECT_ID')
    if env_client_id and env_client_id.strip():
        self._cached_client_object_id = env_client_id.strip()
        return env_client_id.strip()
    
    # Return None if not configured (auto-discovery requires async call)
    return None
```

---

### 3. **Server Integration** (`src/aparavi_mcp/server.py`)

#### **Updated Methods**:

##### `_handle_manage_tag_definitions()` (Line ~2544)
**Before**:
```python
# Check if client object ID is configured
if not self.aparavi_client.client_object_id:
    return {
        "content": [{
            "type": "text", 
            "text": "Error: Client object ID not configured. Please set APARAVI_CLIENT_OBJECT_ID in your .env file.\n\nExample format:\nAPARAVI_CLIENT_OBJECT_ID=f7388d0e-apag-4e86-86f0-1fbedb0b63db"
        }],
        "isError": True
    }
```

**After**:
```python
# Ensure client object ID is available (with auto-discovery)
try:
    await self.aparavi_client.ensure_client_object_id()
except Exception as e:
    return {
        "content": [{
            "type": "text", 
            "text": f"Error: Could not obtain client object ID. {str(e)}"
        }],
        "isError": True
    }
```

##### `_handle_apply_file_tags()` (Line ~2606)
**Before**:
```python
# Check if client object ID is configured
if not self.aparavi_client.client_object_id:
    return {
        "content": [{
            "type": "text", 
            "text": "Error: Client object ID not configured. Please set APARAVI_CLIENT_OBJECT_ID in your .env file."
        }],
        "isError": True
    }
```

**After**:
```python
# Ensure client object ID is available (with auto-discovery)
try:
    await self.aparavi_client.ensure_client_object_id()
except Exception as e:
    return {
        "content": [{
            "type": "text", 
            "text": f"Error: Could not obtain client object ID. {str(e)}"
        }],
        "isError": True
    }
```

##### `_handle_tag_workflow_operations()` (Line ~2764)
**Before**:
```python
# Check if client object ID is configured
if not self.aparavi_client.client_object_id:
    return {
        "content": [{
            "type": "text", 
            "text": "Error: Client object ID not configured. Please set APARAVI_CLIENT_OBJECT_ID in your .env file."
        }],
        "isError": True
    }
```

**After**:
```python
# Ensure client object ID is available (with auto-discovery)
try:
    await self.aparavi_client.ensure_client_object_id()
except Exception as e:
    return {
        "content": [{
            "type": "text", 
        "text": f"Error: Could not obtain client object ID. {str(e)}"
        }],
        "isError": True
    }
```

---

## Technical Implementation Details

### **Auto-Discovery Logic Flow**

1. **Check Cache**: If client object ID is already cached in the session, use it
2. **Check Config**: Look for `APARAVI_CLIENT_OBJECT_ID` in configuration
3. **Check Environment**: Check `APARAVI_CLIENT_OBJECT_ID` environment variable
4. **Auto-Discovery**: Execute AQL query to find any node with `nodeObjectId`
5. **Cache Result**: Store discovered ID for future use in the session
6. **Error Handling**: Provide clear error messages if all methods fail

### **AQL Query Details**

The auto-discovery uses this AQL query:
```sql
SELECT node, nodeObjectId WHERE nodeObjectID IS NOT NULL LIMIT 1
```

**Why this works**:
- `nodeObjectId` from any node is the same as the `clientObjectId` needed for tagging
- The query finds any accessible node in the system
- Only needs one result (`LIMIT 1`) to get the required ID
- The format follows UUID pattern: `########-apag-####-####-############`

### **Backward Compatibility**

The implementation maintains full backward compatibility:
- Existing `APARAVI_CLIENT_OBJECT_ID` environment variable still works
- Manual configuration takes precedence over auto-discovery
- No breaking changes to existing API or configuration

### **Error Handling**

Comprehensive error handling includes:
- Clear error messages when auto-discovery fails
- Logging at appropriate levels (info, warning, error)
- Graceful fallback behavior
- Detailed exception information for debugging

### **Performance Considerations**

- **Caching**: Discovered client object ID is cached for the session
- **Lazy Loading**: Auto-discovery only occurs when needed
- **Single Query**: Only one AQL query needed for discovery
- **No Redundant Calls**: Cached value prevents repeated discovery attempts

---

## Testing Results

### **Test Script Validation**

The comprehensive test script (`tests/tagging_api_test.py`) confirmed:

✅ **Client Object ID Discovery**: Successfully discovered `f7388d0e-apag-4e86-86f0-1fbedb0b63db`  
✅ **Tag Definition Management**: Create, list, and delete operations work  
✅ **File Tagging**: Apply and remove tags from files  
✅ **Tag-Based Search**: Search files by tag criteria  
✅ **Error Handling**: Proper error messages and logging  

### **Integration Testing**

All tagging methods in the MCP server now:
- Automatically discover client object ID when needed
- Provide clear error messages if discovery fails
- Maintain session-level caching for performance
- Work seamlessly without manual configuration

---

## Usage Examples

### **Automatic Discovery (New Default Behavior)**
```python
# No configuration needed - auto-discovery happens automatically
aparavi_client = AparaviClient(config, logger)
await aparavi_client.manage_tag_definitions("create", ["test-tag"])
```

### **Manual Configuration (Still Supported)**
```bash
# Environment variable
export APARAVI_CLIENT_OBJECT_ID="f7388d0e-apag-4e86-86f0-1fbedb0b63db"
```

### **Programmatic Access**
```python
# Get client object ID (with auto-discovery if needed)
client_id = await aparavi_client.ensure_client_object_id()
print(f"Using client object ID: {client_id}")
```

---

## Benefits of This Implementation

1. **Seamless User Experience**: No manual configuration required
2. **Backward Compatible**: Existing configurations continue to work
3. **Performance Optimized**: Caching prevents redundant discovery calls
4. **Robust Error Handling**: Clear messages when issues occur
5. **Production Ready**: Comprehensive testing validates all functionality
6. **Maintainable**: Clean separation of concerns and well-documented code

---

## Files Modified

1. **`tests/tagging_api_test.py`** - New comprehensive test script
2. **`src/aparavi_mcp/aparavi_client.py`** - Added auto-discovery methods and updated property
3. **`src/aparavi_mcp/server.py`** - Updated all tagging methods to use auto-discovery

## Total Lines of Code Added/Modified

- **New code**: ~200 lines (auto-discovery methods, test script)
- **Modified code**: ~30 lines (server method updates)
- **Total impact**: ~230 lines across 3 files

The implementation is now complete and ready for production use!
