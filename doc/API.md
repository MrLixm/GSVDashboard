# API

[![root](https://img.shields.io/badge/back_to_root-536362?)](../README.md)
[![INDEX](https://img.shields.io/badge/index-4f4f4f?labelColor=blue)](INDEX.md)
[![API](https://img.shields.io/badge/api-fcb434)](API.md)

# ![module](https://img.shields.io/badge/module-5663B3) `GSV`

## ![class](https://img.shields.io/badge/class-6F5ADC) `GSV.GSVSettings`

A regular dictionary object with a fixed structure. Structure is verified
through `validate()` method.

Used to configure the output result of the scene parsing.

In GSVDb, the GSVSettings is built live from various parameters except for
the `nodes` key. For this one the values from `__default` are used.

### ![attribute](https://img.shields.io/badge/attribute-4f4f4f) `GSV.GSVSettings.__default`

Default structure used for self.

### ![attribute](https://img.shields.io/badge/attribute-4f4f4f) `GSV.GSVSettings.__expected`

Used partially by `validate()` to determine if self structure is valid.

### ![method](https://img.shields.io/badge/method-4f4f4f) `GSV.GSVSettings.__init__`

Init is similar to a traditional dictionnary :

- You can pass no arguments, in that case the dictionnary is initialized with
a default structure (see `__default` attribute).

- You can pass a dictionnary with the structure already built. This will call
`validate()` to check if the structure is valid. 

### ![method](https://img.shields.io/badge/method-4f4f4f) `GSV.GSVSettings.validate`

Called every time self structure change. Raise an assertion error is the 
structure is not valid.

### ![howto](https://img.shields.io/badge/howto-418F55) Add support for a new node

As mention above, GSVDb used the `__default` attribute `nodes` key. To add
a new node you need to extend this key's dictionnary. Supported nodes are 
registered by node types, so add a new key with your node's type. The value
is then a dict of 2 keys.

- First key `"action"` determine what action is performed by your node on the GSV
. It can set it `"setter"` or only use its value `"getter"` 
(For now, a node can't do both).

- Second key `"structure"` is a function that once called, return a dictionnary
of GSV names with their associated list of value. Have a look at the existing 
functions to understand what to return. Function's signature should look like :

```
Args:
    knode(NodegraphAPI.Node): 
        current node of the corresponding type being visited
Returns:
    dict of str:
        keys are GSV names this node is using,
        values for each key must be a list of string corresponding to the values
            used by this GSV. 
```

## ![class](https://img.shields.io/badge/class-6F5ADC) `GSV.GSVNode`
## ![class](https://img.shields.io/badge/class-6F5ADC) `GSV.GSVObject`
## ![class](https://img.shields.io/badge/class-6F5ADC) `GSV.GSVScene`


---
[![root](https://img.shields.io/badge/back_to_root-536362?)](../README.md)
[![INDEX](https://img.shields.io/badge/index-4f4f4f?labelColor=blue)](INDEX.md)
[![API](https://img.shields.io/badge/api-fcb434)](API.md)