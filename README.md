# mib-xml 解析器

独立工程，不依赖 CCU / Maven。CCU 运行时不跑本解析器；Java 产物尚未接入 Maven。

## 源文件命名（必为 `.xml`）

`mib-xml/` 里可以放多份，**每份一个文件名、后缀必须是 `.xml`**：

| 角色 | 命名 | 例子 |
|------|------|------|
| 源 XML（开发者提供） | `{模块名}.xml` | `1202v0328-mib.xml`、`1201.xml` |
| 精简 XML（生成，勿手改） | `{模块名}-parse.xml` | `1202v0328-mib-parse.xml` |
| Java 实体（生成） | `entities/{模块名}/` | `entities/1202v0328-mib/` |

`{模块名}` 就是去掉 `.xml` 的文件名，必须互不相同。无参执行会解析文件夹里**全部**源 `.xml`，自动跳过 `*-parse.xml`。多份互不影响：各有自己的 `-parse.xml` 和 `entities/{模块名}/`。

不要用无后缀的 `1202v0328-mib`，也不要把精简结果再当源文件。

## 默认目录

```text
py -3 parse_mib_xml.py
```

| | 默认路径（相对 `model-ntcip/`） |
|--|--|
| 输入文件夹 | `mib-xml/`（只认 `*.xml`，跳过 `*-parse.xml`） |
| 精简 XML | `mib-xml/{模块名}-parse.xml` |
| Java 实体 | `entities/{模块名}/` |

例如 `mib-xml/1202v0328-mib.xml` → `1202v0328-mib-parse.xml` + `entities/1202v0328-mib/`。

`phaseWalk` 注解 OID：`1.3.6.1.4.1.1206.4.2.1.1.2.1.2`；`SplitEntry` indexes：`splitNumber, splitPhase`。

## 覆盖默认

```text
py -3 parse_mib_xml.py -i <文件或文件夹> [-o <输出目录>]
```

- `-i` 文件：只解析这一份（必须是 `.xml`）；文件夹：该目录下全部源 `.xml`。
- `-o` 指定后，精简 XML 和 Java 都写到该目录（测试用）。
