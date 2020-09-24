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

class MyModel(Schema):
    name: str

async def main():
    store = await Store.create("./data/my_store", schema=MyModel)
```

Use [Pydantic][] to define your models. When this store is initialized, it will create the directory `${cwd}/data/my_store` if it doesn't already exist.

[pydantic]: https://pydantic-docs.helpmanual.io/

### Add items to the store

```py
async def main():
    item = MyModel(name="fizzbuzz")
    store = await Store.create("./data/my_store", schema=MyModel)

    # add an item to the store
    item_key = await store.add(item)
```

The store has three methods that may add an item:

- `store.add` - Adds an item to the store as long as the item's key doesn't already exist
- `store.put` - Adds an item to the store or updates an existing item if the key already exists
- `store.ensure` - Get an item by key, inserting a default value if the key doesn't exist

By default, the store will generate a UUID for the key and create a JSON file using that key as the filename.

- Directory: `{cwd}/data/my_store`
  - File: `{item_key}.json`
    - Contents: `{ "name": "fizzbuzz" }`

### Add items to the store with a specific key

There are two ways to insert items into the store with a specific key:

- Pass a key paramter to `add`, `put`, or `ensure`
  - `key = await store.put(item, key)`
  - `item = await store.ensure(key, default_item)`
- Initialize the store with the `primary_key` option
  - `Store.create("my_store", schema=MyModel, primary_key="name")`
  - When inserting items, the store will read `item[primary_key]` and use that as the key

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

async def main():
    store = await Store.create("/path/to/directory")
```

Creates a `Store` instance to store items in a given directory. Do not configure multiple stores for the same directory at the same time.

Unless otherwise noted, all methods of a `Store` are `async` and should be `await`ed.

### store.add(item: Schema, key: Optional[str] = None) -> Optional[str]

| argument | type     | required | description                      |
| -------- | -------- | -------- | -------------------------------- |
| `item`   | `Schema` | Yes      | Item to serialize and store      |
| `key`    | `str`    | No       | Key - generated UUIDv4 if `None` |

```py
from junk_drawer import Store, Schema

class Scissors(Schema):
  left_handed: bool

async def main():
    store = await Store.create("scissors", schema=Scissors)
    scissors = Scissors(left_handed=true)
    scissors_key = await store.add(scissors)
```

Adds an item into the store, serializing `item` to JSON and placing it in `${store_name}/${key}.json`. If an item at `key` already exists, `add` will not insert `item` and will return `None`.

### store.put(item: Schema, key: Optional[str] = None) -> str

| argument | type     | required | description                      |
| -------- | -------- | -------- | -------------------------------- |
| `item`   | `Schema` | Yes      | Item to serialize and store      |
| `key`    | `str`    | No       | Key - generated UUIDv4 if `None` |

```py
from junk_drawer import Store

class Scissors(Schema):
  left_handed: bool

async def main():
    store = await Store.create("scissors", schema=Scissors)
    scissors = Scissors(left_handed=true)
    scissors_key = await store.put(scissors, "my_scissors")
```

Adds an item into the store, serializing `item` to JSON and placing it in `${store_name}/${key}.json`. Will replace the item with `key` if it already exists.

### store.get(key: str) -> Optional[Schema]

| argument | type  | required | description     |
| -------- | ----- | -------- | --------------- |
| `key`    | `str` | No       | Key to retrieve |

```py
from junk_drawer import Store

class Scissors(Schema):
  left_handed: bool

async def main():
    store = await Store.create("scissors", schema=Scissors)
    scissors = await store.get("my_scissors")
```

Get an item by key from the store. Returns `None` if no item with that key exists.

### store.ensure(key: str, default_item: Schema) -> Schema

| argument       | type     | required | description                      |
| -------------- | -------- | -------- | -------------------------------- |
| `key`          | `str`    | No       | Key to retrieve                  |
| `default_item` | `Schema` | Yes      | Item to insert if key is missing |

```py
from junk_drawer import Store

class Scissors(Schema):
  left_handed: bool

async def main():
    store = await Store.create("scissors", schema=Scissors)
    default_scissors = Scissors(left_handed=true)
    scissors = await store.ensure("my_scissors", default_scissors)
```

Get an item by key from the store. If no item with that key exists, adds `default_item` to the store with `key`.

### store.get_all_items() -> List[Schema]

```py
from junk_drawer import Store

class Scissors(Schema):
  left_handed: bool

async def main():
    store = await Store.create("scissors", schema=Scissors)
    all_scissors = await store.get_all_items()
```

Returns a list of all items in the store. Returns keys in the same order as `get_all_keys`.

### store.get_all_keys() -> List[str]

```py
from junk_drawer import Store

class Scissors(Schema):
  left_handed: bool

async def main():
    store = await Store.create("scissors", schema=Scissors)
    all_scissor_keys = await store.get_all_keys()
```

Returns a list of all keys in the store. Returns keys in the same order as `get_all_items`.

### store.count() -> int

```py
from junk_drawer import Store

class Scissors(Schema):
  left_handed: bool

async def main():
    store = await Store.create("scissors", schema=Scissors)
    n_scissors = await store.count()
```

Returns the number of items in the store.

### store.delete(key: str) -> Optional[str]

| argument | type  | required | description           |
| -------- | ----- | -------- | --------------------- |
| `key`    | `str` | Yes      | Document ID to delete |

```py
from junk_drawer import Store

class Scissors(Schema):
  left_handed: bool

async def main():
    store = await Store.create("scissors", schema=Scissors)
    scissors_key = await store.put(Scissors(left_handed=true))
    await store.delete(scissors_key)
```

Removes the document with key `key` from the store. Returns the ID of the document it removed, if any.

### Migration

A `Migration` is a function that takes a `Dict[str, Any]` and returns a `Dict[str, Any]`

```py
Migration = Callable[[Dict[str, Any]], Dict[str, Any]]
```
