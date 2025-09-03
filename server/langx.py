import os, uuid, json, textwrap, time
from typing import Any, Dict, List, Optional, Generator

import langextract as lx

MODEL_ID = os.environ.get("LX_MODEL_ID", "openai:gpt-5-mini")

DEFAULT_PROMPT = textwrap.dedent("""Извлеки из текста именованные сущности (organization, person, date, money) и отношения между ними.
Строго используй текст источника (не перефразируй). Верни атрибуты: type, value, optional_attrs.
""")

def _examples_default():
    return [lx.data.ExampleData(
        text="Компания ACME выручила $12.4M во 2 квартале 2025 года.",
        extractions=[
            lx.data.Extraction(extraction_class="organization", extraction_text="ACME"),
            lx.data.Extraction(extraction_class="money", extraction_text="$12.4M", attributes={"period":"Q2 2025"}),
        ],
    )]

def run_extraction(text_or_url: str, prompt: Optional[str]=None, examples: Optional[List[Dict[str, Any]]]=None) -> Dict[str, Any]:
    prompt = prompt or DEFAULT_PROMPT
    ex = _examples_default()
    if examples:
        ex = [lx.data.ExampleData(
                text=e.get("text",""),
                extractions=[lx.data.Extraction(extraction_class=it.get("class","entity"), extraction_text=it.get("text",""), attributes=it.get("attributes",{}))
                             for it in e.get("extractions",[])]
             ) for e in examples]

    result = lx.extract(
        text_or_documents=text_or_url,
        prompt_description=prompt,
        examples=ex,
        model_id=os.getenv("LX_MODEL_ID", "openai:gpt-5-mini"),
        api_key=os.getenv("OPENAI_API_KEY"),
        fence_output=True,
        use_schema_constraints=False,
    )
    
    job_id = uuid.uuid4().hex[:8]
    out_dir = os.path.join("data", "extracts", job_id); os.makedirs(out_dir, exist_ok=True)
    lx.io.save_annotated_documents([result], output_name="result.jsonl", output_dir=out_dir)
    html = lx.visualize(os.path.join(out_dir, "result.jsonl"))
    with open(os.path.join(out_dir, "viz.html"), "w", encoding="utf-8") as f:
        f.write(html.data if hasattr(html, 'data') else html)
    flat = []
    for doc in result.documents:
        for ann in doc.annotations:
            flat.append({"class": ann.extraction_class, "text": ann.extraction_text, "attributes": ann.attributes or {}, "doc_char_start": ann.char_start, "doc_char_end": ann.char_end})
    return {"job_id": job_id, "items": flat}

def stream_extraction(text_or_url: str, prompt: Optional[str]=None) -> Generator[Dict[str, Any], None, None]:
    start = time.time()
    yield {"event":"start","t":0}
    time.sleep(0.2); yield {"event":"fetch","msg":"Получаем документ","t":time.time()-start}
    time.sleep(0.2); yield {"event":"analyze","msg":"LLM извлекает сущности","t":time.time()-start}
    res = run_extraction(text_or_url, prompt=prompt)
    time.sleep(0.2); yield {"event":"save","msg":"Сохраняем JSONL и визуализацию","t":time.time()-start,"job_id":res["job_id"]}
    time.sleep(0.2); yield {"event":"done","result":res,"t":time.time()-start}
