# junk-drawer

> Simple JSON data storage on the filesystem

`junk_drawer` is a Python module to place JSON-serializable objects in a key-value store, backed by JSON-on-the-filesystem in a simple directory structure.

**Work in progress - Not yet available**

## install

```shell
pip install junk-drawer
```

## Usage

### Create a store with a schema

```py
from junk_drawer import Store
from pydantic import BaseModel

class MyModel(BaseModel):
    name: str

async def main():
    store = await Store.create("path/to/store", schema=MyModel)
```

Use [Pydantic][] to define your models. When this store is initialized, it will create the directory `${cwd}/path/to/store` if it doesn't already exist.

[pydantic]: https://pydantic-docs.helpmanual.io/

### Get an item from the store

```py
async def main():
    item = MyModel(name="fizzbuzz")
    store = await Store.create("path/to/store", schema=MyModel)
    item = await store.get("some-key")
```

The store has the following methods for getting items and keys from the store.

- `store.get(key)`
  - Gets an item by key from the store, if that key exists and item passes validation
- `store.exists(key)`
  - Checks whether a given key exists in the store (does not read or check the item itself)
- `store.get_all_items()`
  - Returns all items in the store
- `store.get_all_keys()`
  - Returns all items in the store
- `store.get_all_entries()`
  - Returns all items in the store zipped in tuples with their keys

### Add an item to the store

```py
async def main():
    item = MyModel(name="fizzbuzz")
    store = await Store.create("path/to/store", schema=MyModel)
    item_key = await store.add(item, "some-key")
```

The store has the following methods that may add an item at a specific key. The key will be used as the name of the JSON file and **should not begin with a dot**.

- `store.add(item, key)`
  - Adds an item to the store as long as the item's key doesn't already exist
- `store.put(item, key)`
  - Adds an item to the store or updates an existing item if the key already exists
- `store.ensure(default_item, key)`
  - Gets an item by key, inserting a default value if the key doesn't exist
  - Basically a shortcut for `get` followed by `add` if `get` returned `None`

The snippet above will create the following directory and file:

Directory: `{cwd}/path/to/store`

- File: `some-key.json`
  - Contents: `{ "name": "fizzbuzz" }`

#### Add an item using key from model

```py
class KeyedModel(BaseModel):
    uid: UUID
    name: str

async def main():
    item = ModelWithKey(uid=uuid4(), name="fizzbuzz")
    store = await Store.create("store", schema=KeyedModel, primary_key="uid")
    item_key = await store.add(item)
```

If you specify the `primary_key` option when creating the store, `add`, `put`, and `ensure` will use the value of `primary_key` from the item to determine the key. The value of `primary_key` will be converted to a `str` before use and **should not begin with a dot**.

### Remove an item from the store

```py
async def main():
    item = MyModel(name="fizzbuzz")
    store = await Store.create("path/to/store", schema=MyModel)

    removed_key = await store.delete("some-key")
```

If you specify the `primary_key` option when creating the store, store modification operations will use the value of `primary_key` from the item to determine the key. The value of `primary_key` will be converted to a `str` before use and **should not begin with a dot**.

- `store.add(item)`
- `store.put(item)`
- `store.ensure(default_item)`

### Migrate schemas

```py
class MyModel(BaseModel):
    # present the first time store was used (schema v0)
    name: str
    # added in schema v1
    new_field: str
    # added in schema v2
    another_new_field: int

def migration_v1(prev: Dict[str, Any]) -> Dict[str, Any]:
    next_model = prev
    next_model["new_field"] = "default_value"
    return next_model

def migration_v2(prev: Dict[str, Any]) -> Dict[str, Any]:
    next_model = prev
    next_model["another_new_field"] = 42
    return next_model

async def main():
    store = await Store.create(
        "./data/existing_store",
        schema=MyModel,
        migrations=(migration_v1, migration_v2)
    )
```

If you need to change the schema of items in an already existing store, you need to add a migration. A migration is a function that takes the previous version of the item as a plain-old-Python-dict and returns the new version of the item as a dict.

The store can be initialized with a list of migration functions, where each function represents one version of the schema. The migration functions will be called as a waterfall, and the last function in the chain **must output a dict in the correct format**. Pydantic will raise an error if the dict cannot be used to successfully initialize a model instance.

The store will **migrate all existing documents when the store is initialized**.

## Reference

### Store.create(name, schema, primary_key = None, migrations=()) -> Store

| argument      | type              | required | description                                   |
| ------------- | ----------------- | -------- | --------------------------------------------- |
| `name`        | `str`             | Yes      | Store name used as the store's root directory |
| `schema`      | `Type[BaseModel]` | Yes      | Document schema                               |
| `primary_key` | `str`             | No       | Primary key field in `schema`, if applicable  |
| `migrations`  | `List[Migration]` | No       | List of schema migration functions            |

```py
from junk_drawer import Store
from pydantic import BaseModel

class MyModel(BaseModel):
    name: str

async def main():
    store = await Store.create("path/to/store", schema=MyModel)
```

Creates a `Store` instance to store items in a given directory relative to the current working directory. Do not configure multiple stores for the same directory.

Unless otherwise noted, all methods of a `Store` are `async` and should be `await`ed.

### store.get(key: str) -> Optional[BaseModel]

| argument | type  | required | description     |
| -------- | ----- | -------- | --------------- |
| `key`    | `str` | No       | Key to retrieve |

```py
from junk_drawer import Store
from pydantic import BaseModel

class Scissors(BaseModel):
  left_handed: bool

async def main():
    store = await Store.create("scissors", schema=Scissors)
    scissors = await store.get("my-scissors")
```

Get an item by key from the store. Returns `None` if no item with that key exists.

### store.ensure(default_item: BaseModel, key: Optional[str] = None) -> BaseModel

| argument       | type        | required | description                                    |
| -------------- | ----------- | -------- | ---------------------------------------------- |
| `default_item` | `BaseModel` | Yes      | Item to insert if key is missing               |
| `key`          | `str`       | No       | Key, optional if using `primary_key` from item |

```py
from junk_drawer import Store
from pydantic import BaseModel

class AppConfig(BaseModel):
  opted_in: bool

async def main():
    default_config = AppConfig(opted_in=false)
    store = await Store.create("config", schema=AppConfig)
    config = await store.ensure(default_config, "index")
```

Get an item by key from the store. If no item with that key exists, adds `default_item` to the store before returning the item. Effectively a shortcut for a `get` followed by an `add` if the `get` returns `None`.

### store.get_all_items() -> List[BaseModel]

```py
from junk_drawer import Store
from pydantic import BaseModel

class Scissors(BaseModel):
  left_handed: bool

async def main():
    store = await Store.create("scissors", schema=Scissors)
    all_scissors = await store.get_all_items()
```

Returns a list of all items in the store. If items are not using a `primary_key`, use `get_all_entries` to get items and their associated keys.

### store.get_all_keys() -> List[str]

```py
from junk_drawer import Store
from pydantic import BaseModel

class Scissors(BaseModel):
  left_handed: bool

async def main():
    store = await Store.create("scissors", schema=Scissors)
    all_scissor_keys = await store.get_all_keys()
```

Returns a list of all keys in the store. May return more keys than actual valid documents if there are invalid JSON files in the store directory.

### store.get_all_entries() -> List[Tuple[str, BaseModel]]

```py
from junk_drawer import Store
from pydantic import BaseModel

class Scissors(BaseModel):
  left_handed: bool

async def main():
    store = await Store.create("scissors", schema=Scissors)
    all_scissor_entries = await store.get_all_entries()
```

Returns a zipped list of all key/item pairs in the store. Useful if you're not using `primary_key` but you still need to get all items and their associated keys.

### store.add(item: BaseModel, key: Optional[str] = None) -> Optional[str]

| argument | type        | required | description                                    |
| -------- | ----------- | -------- | ---------------------------------------------- |
| `item`   | `BaseModel` | Yes      | Item to serialize and store                    |
| `key`    | `str`       | No       | Key, optional if using `primary_key` from item |

```py
from junk_drawer import Store
from pydantic import BaseModel

class Scissors(BaseModel):
  left_handed: bool

async def main():
    store = await Store.create("scissors", schema=Scissors)
    scissors = Scissors(left_handed=true)
    scissors_key = await store.add(scissors, "my-scissors")
```

Adds an item into the store, serializing `item` to JSON and placing it in `${store_name}/${key}.json`. If an item at `key` already exists, `add` will not insert `item` and will return `None`.

### store.put(item: BaseModel, key: Optional[str] = None) -> str

| argument | type        | required | description                                    |
| -------- | ----------- | -------- | ---------------------------------------------- |
| `item`   | `BaseModel` | Yes      | Item to serialize and store                    |
| `key`    | `str`       | No       | Key, optional if using `primary_key` from item |

```py
from junk_drawer import Store
from pydantic import BaseModel

class Scissors(BaseModel):
  left_handed: bool

async def main():
    store = await Store.create("scissors", schema=Scissors)
    scissors = Scissors(left_handed=true)
    scissors_key = await store.put(scissors, "my-scissors")
```

Adds an item into the store, serializing `item` to JSON and placing it in `${store_name}/${key}.json`. Will replace the item with `key` if it already exists.

### store.delete(key: str) -> Optional[str]

| argument | type  | required | description           |
| -------- | ----- | -------- | --------------------- |
| `key`    | `str` | Yes      | Document ID to delete |

```py
from junk_drawer import Store
from pydantic import BaseModel

class Scissors(BaseModel):
  left_handed: bool

async def main():
    store = await Store.create("scissors", schema=Scissors)
    scissors_key = await store.put(Scissors(left_handed=true), "key")
    await store.delete(scissors_key)
```

Removes the document with key `key` from the store. Returns the ID of the document it removed, if any.

### Migration

A `Migration` is a function that takes a `Dict[str, Any]` and returns a `Dict[str, Any]`

```py
Migration = Callable[[Dict[str, Any]], Dict[str, Any]]
```
