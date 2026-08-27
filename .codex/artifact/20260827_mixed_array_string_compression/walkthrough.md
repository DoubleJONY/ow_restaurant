# Workshop Mixed Array String Compression

## Motivation

Overwatch Workshop's element limit makes large literal `Array(...)` tables expensive because each array entry consumes elements. A `Mapped Array` decoded from `String Split(Custom String(...))` is substantially cheaper because the encoded payload is carried by a small number of `Custom String` expressions.

Earlier compression work left mixed-type tables such as `CUTTING_RESULT` raw because some indices contain nested values such as `Array(a, b)`. This session established a compatibility-preserving way to compress those tables as well.

## Compatibility Strategy

1. Encode `False` and every nested-array slot as `0` in the slash-delimited numeric string.
2. Decode the string with the existing temporary numeric lookup:

```ow
Mapped Array(
    String Split(..., Custom String("/")),
    Index Of Array Value(Global.MIXING_RECIPE, Current Array Element)
)
```

3. Restore each nested value immediately afterward with an indexed assignment:

```ow
Global.CUTTING_RESULT[index] = Array(a, b);
```

This preserves the final runtime shape expected by existing consumers:

- scalar results keep `Count Of(...) == 0`
- multi-result entries keep `Count Of(...) > 1`
- existing `First Of(...)` and `Last Of(...)` logic remains unchanged

The same strategy was applied to `ADDITIONAL_MATERIAL_LIST`, including entries with two or three material codes.

## Initialization Ordering

The temporary numeric `Global.MIXING_RECIPE` lookup must still contain the string values `0..N` while both tables are decoded. `ADDITIONAL_MATERIAL_LIST` originally appeared after `Global.MIXING_RECIPE` had been replaced with the real mixing graph, so its compressed initialization was moved before this overwrite:

```ow
Global.MIXING_RECIPE = Mapped Array(Global.ITEM_NAME, Empty Array);
```

No gameplay consumer was moved or changed.

## Data Grouping and Reuse

All files were decoded and compared before editing. Both target tables were identical within these groups, so each group reused one generated representation:

| Group | Files | Entries |
| --- | --- | ---: |
| Restaurant | `ko.ow`, `en.ow`, `jp.ow` | 475 |
| Cafe | `cafe_kr.ow`, `cafe_en.ow`, `kr_deluxe.ow` | 398 |
| GC | `gc_kr.ow`, `gc_en.ow` | 462 |
| N3 | `n3_kr.ow` | 514 |

`kc_kr.ow` had a distinct 343-entry data set and no existing temporary numeric lookup. It was explicitly excluded by the user and remains unchanged.

## Generated Shape

| Group | `CUTTING_RESULT` strings | Nested patches | `ADDITIONAL_MATERIAL_LIST` strings | Nested patches |
| --- | ---: | ---: | ---: | ---: |
| Restaurant | 13 | 20 | 12 | 12 |
| Cafe | 11 | 2 | 11 | 0 |
| GC | 12 | 6 | 12 | 1 |
| N3 | 13 | 6 | 14 | 1 |

All generated string segments were kept at 89 characters or fewer, matching the workspace convention of keeping segments around 90 characters.

## Files Changed

- `ko.ow`
- `en.ow`
- `jp.ow`
- `cafe_kr.ow`
- `cafe_en.ow`
- `kr_deluxe.ow`
- `gc_kr.ow`
- `gc_en.ow`
- `n3_kr.ow`

All modified files use version `v260827`. `kc_kr.ow` remains on its existing version and raw-array representation.

## Validation

For every modified file:

- reconstructed every entry from the generated string chunks and indexed nested-array patches
- compared all reconstructed values and nested-array shapes against the pre-edit table
- confirmed zero mismatches across both tables
- confirmed the expected entry count for its edition
- confirmed the numeric lookup is initialized before both mapped tables
- confirmed both mapped tables are initialized before `Global.MIXING_RECIPE` is overwritten with the real mixing graph
- confirmed no raw assignment remains for either target table
- confirmed every generated string segment is at most 90 characters
- confirmed all version strings are `v260827`
- normalized and verified CRLF line endings

## Remaining Risk

No in-game Workshop import or runtime test was performed. Static reconstruction proves that the final table values and nested-array shapes match the originals, but an in-game check is still recommended to confirm Workshop parser acceptance and runtime behavior under the element limit.
