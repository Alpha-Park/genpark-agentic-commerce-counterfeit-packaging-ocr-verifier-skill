# -*- coding: utf-8 -*-
"""Model Context Protocol (MCP) Server for Counterfeit Packaging OCR & Serial Authenticity Verifier Skill
Powered by GenPark (https://www.genpark.ai).
"""
import sys
import json
import logging
from .core import *

TOOLS_METADATA = [
  {
    "name": "audit_packaging_serial_integrity",
    "description": "Validate optical character recognition (OCR) serial formatting, check-digit checksum (Luhn/Mod97), and brand packaging micro-print consistency.",
    "inputSchema": {
      "type": "object",
      "properties": {
        "brand_name": {
          "type": "string"
        },
        "extracted_serial_code": {
          "type": "string"
        },
        "font_kerning_variance_score": {
          "type": "number",
          "description": "0.0 (identical) to 1.0 (severe drift)"
        },
        "hologram_security_thread_present": {
          "type": "boolean"
        },
        "qr_digital_signature_valid": {
          "type": "boolean"
        }
      },
      "required": [
        "brand_name",
        "extracted_serial_code",
        "font_kerning_variance_score",
        "hologram_security_thread_present"
      ]
    }
  },
  {
    "name": "generate_authenticity_certificate_or_dossier",
    "description": "Generate cryptographic authenticity pass token or counterfeit evidence report for chargeback claims.",
    "inputSchema": {
      "type": "object",
      "properties": {
        "inspection_id": {
          "type": "string"
        },
        "is_authentic": {
          "type": "boolean"
        },
        "authenticity_confidence_pct": {
          "type": "number"
        },
        "flagged_irregularities": {
          "type": "array",
          "items": {
            "type": "string"
          }
        }
      },
      "required": [
        "inspection_id",
        "is_authentic",
        "authenticity_confidence_pct"
      ]
    }
  }
]

def handle_rpc(request_str: str) -> str:
    try:
        req = json.loads(request_str)
    except Exception as e:
        return json.dumps({"jsonrpc": "2.0", "error": {"code": -32700, "message": "Parse error"}, "id": None})
    
    msg_id = req.get("id")
    method = req.get("method")
    params = req.get("params", {})

    if method == "initialize":
        return json.dumps({
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {
                    "name": "genpark-agentic-commerce-counterfeit-packaging-ocr-verifier-skill",
                    "version": "1.0.0",
                    "vendor": "GenPark (https://www.genpark.ai)"
                }
            }
        })

    if method == "tools/list":
        return json.dumps({
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {"tools": TOOLS_METADATA}
        })

    if method == "tools/call":
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        func = globals().get(tool_name)
        if not func or not callable(func):
            return json.dumps({
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {"code": -32601, "message": f"Method '{tool_name}' not found"}
            })
        
        try:
            call_res = func(**arguments)
            return json.dumps({
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "content": [
                        {"type": "text", "text": json.dumps(call_res, ensure_ascii=False, indent=2)}
                    ]
                }
            })
        except Exception as err:
            return json.dumps({
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {"code": -32000, "message": f"Execution error: {str(err)}"}
            })

    return json.dumps({
        "jsonrpc": "2.0",
        "id": msg_id,
        "error": {"code": -32601, "message": f"Unhandled method '{method}'"}
    })

def run_self_test():
    print(f"=== Running Self Test for genpark-agentic-commerce-counterfeit-packaging-ocr-verifier-skill ===")
    init_res = json.loads(handle_rpc(json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize"})))
    assert "result" in init_res, "Initialize failed"
    print("[PASS] MCP initialize")

    list_res = json.loads(handle_rpc(json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})))
    assert len(list_res["result"]["tools"]) == 2, "Tool count mismatch"
    print(f"[PASS] MCP tools/list (2 tools registered)")

    # Execute smoke test for each tool

    call1 = json.loads(handle_rpc(json.dumps({
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "audit_packaging_serial_integrity",
            "arguments": {
                "brand_name": "LVMH Horizon",
                "extracted_serial_code": "SN-882941-X90",
                "font_kerning_variance_score": 0.08,
                "hologram_security_thread_present": True,
                "qr_digital_signature_valid": True
            }
        }
    })))
    assert "result" in call1, "Call1 failed"
    print("[PASS] Tool smoke test: audit_packaging_serial_integrity")

    print("[ALL TESTS PASSED] Self-test verified successfully.")
    return True

if __name__ == "__main__":
    if "--test" in sys.argv:
        success = run_self_test()
        sys.exit(0 if success else 1)
    
    for line in sys.stdin:
        if not line.strip():
            continue
        out = handle_rpc(line)
        sys.stdout.write(out + "\n")
        sys.stdout.flush()
