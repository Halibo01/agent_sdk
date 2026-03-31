---
title: Grammar Builder (Structured Outputs) | Agent SDK
description: Learn how to force LLMs to output strict JSON, XML, YAML, and Markdown formats using GrammarBuilder.
keywords: 
    - structured outputs
    - grammar
    - json mode
    - gbnf
    - gbnf
    - strict generation
---

# GrammarBuilder (Structured Outputs)

LLMs are inherently trained to generate free-flowing natural language. However, when building enterprise applications or data-extraction pipelines, you often need the AI to output exactly the format your system expects (like JSON, XML, or CSV) without any conversational filler or hallucinations.

The `GrammarBuilder` is a powerful engine inside Agent SDK that solves this problem. It takes standard Python type hints (like `str`, `int`, `list`, `dict`) and compiles them into **GBNF (Context-Free Grammar)** rules. 

When you attach this grammar to an agent, it mathematically restricts the tokens the LLM is allowed to generate, reducing formatting errors to **0%**.

---

## Example 1: Basic JSON and XML Outputs

The easiest way to use the GrammarBuilder is to pass standard Python types inside a dictionary schema. The builder supports `str`, `int`, `float`, and `bool` natively.

```python
from agent_sdk.grammar import GrammarBuilder

builder = GrammarBuilder()

# 1. Define your strict schema using Python types
schema = dict(
    store=dict(
        store_name=str,
        is_open=bool,
        daily_revenue=float,
        inventory_count=int
    )
)

# 2. Compile into JSON constraints
json_gbnf = builder.to_json(**schema)
print("JSON GBNF Rule:")
print(json_gbnf)

# 3. Or compile the exact same schema into XML constraints!
xml_gbnf = builder.to_xml(root_tag="store_data", **schema)
```

---

## Example 2: Lists and Optionals (Union Types)

Real-world data often involves arrays (lists of items) and optional fields. The `GrammarBuilder` fully supports Python's `list` and Union types (`| None` or `Optional`).

```python
from agent_sdk.grammar import GrammarBuilder

builder = GrammarBuilder()

# 1. Complex Schema with Lists and Optionals
schema = dict(
    employee_directory=list[dict(          # Forces an array of objects
        full_name=str,
        age=int | None,                    # Can be an integer or null (optional)
        has_admin_rights=bool
    )]
)

yaml_gbnf = builder.to_yaml(**schema)
print(yaml_gbnf)
```

In the example above, the AI is forced to output an array of dictionaries. If it reaches the `age` field, it is physically forced to either output numbers (`[0-9]+`) or the word `"null"`.

---

## Example 3: Literals and Custom Tokens (Advanced)

Sometimes, you don't just want *any* string; you want specific words or specific regex patterns (like emails or hex codes). 

You can use `typing.Literal` to restrict choices, or use `builder.register_type()` to inject your own custom Regex patterns directly into the engine.

```python
from agent_sdk.grammar import GrammarBuilder
import typing

builder = GrammarBuilder()

# 1. Add a raw composite token
builder.add_token("currency_symbol", '"$" | "€" | "₺"')

# 2. Register a custom type (e.g., precise Price format)
# Rule: Symbol followed by numbers, a dot, and exactly 2 decimal digits
builder.register_type("price", "price_val", 'currency_symbol [0-9]+ "." [0-9]{2}')

# 3. Override standard string to only allow A-Z letters
builder.custom_string_regex = '"\\"" [a-zA-Z ]+ "\\""'

schema = dict(
    receipt=list[dict(
        item_name=str,                                  # Will now only accept letters!
        item_cost=builder.price,                        # Our custom Regex rule!
        category=typing.Literal["food", "electronics"]  # The AI MUST choose one of these words
    )]
)

print(builder.to_json(**schema))
```

---

## Example 4: Markdown Table Output

The `GrammarBuilder` can also generate grammar rules that force the LLM to output a strict Markdown table. Use `to_markdown_table()` to define columns and their types. The builder will produce a table with a header row, separator row, and one or more data rows constrained to your schema.

```python
from agent_sdk.grammar import GrammarBuilder

builder = GrammarBuilder()

# Define a table schema: a list of row dictionaries
schema = dict(
    rows=list[dict(
        product=str,
        price=float,
        in_stock=bool
    )]
)

md_grammar = builder.to_markdown_table(**schema)
print(md_grammar)
```

This will force the model to output a well-formed Markdown table like:

```
| product | price | in_stock |
|---|---|---|
| Widget | 9.99 | true |
```

---

## Example 5: Using Grammar in Agents

Once you have built your schema, you can attach it directly to an `Agent`. 

When you provide the `output_schema` and `output_format` parameters, the `Agent` will automatically append strict instructions to its system prompt, ensuring the AI knows exactly what format it is locked into.

*(Note: For API providers like OpenAI and Gemini, this acts as an unbreakable system prompt instruction. For local engines like `llama.cpp` or `Ollama`, this GBNF string can be passed directly to their grammar decoders).*

```python
from agent_sdk import Runner, Agent
from agent_sdk.clients.openai import OpenAIClient
from agent_sdk.grammar import GrammarBuilder
import typing

# 1. Build the schema
builder = GrammarBuilder()
schema = builder.to_xml(
    root_tag="user_profile",
    user=dict(
        name=str,
        role=typing.Literal["admin", "user", "guest"]
    )
)

# 2. Attach the schema to the Agent
extractor_agent = Agent(
    name="DataExtractor",
    model="gpt-4o-mini",
    instructions="You extract user data from text.",
    output_schema=schema,    # Injects the GBNF rules
    output_format="xml"      # Automatically adds: "CRITICAL: You must output strictly in XML"
)

# 3. Run the Agent
client = OpenAIClient(api_key="your-api-key")
runner = Runner(client)

# The agent will process the text and return guaranteed XML matching your exact schema!
events = runner.run_stream(extractor_agent, "Extract John Doe. He is an admin.")
for event in events:
    if event.type == "token":
        print(event.data, end="")
```
