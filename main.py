import os
import time
import json
import requests

BASE_OUTPUT_DIR = "matches_json_categorized"

# マップサイズごとのファイル連番を管理する辞書
counters = {}

START_ID = 1271
END_ID = 0

for match_id in range(START_ID, END_ID - 1, -1):
    url = f"https://procon37arena.online/api/matches/{match_id}"
    print(f"[{match_id}] 取得中: {url}")
    
    try:
        response = requests.get(url, timeout=10)
        
        if response.status_code != 200:
            print(f"  -> [スキップ] ステータス: {response.status_code}")
            time.sleep(1.5)
            continue
            
        data = response.json()
        
        if "problem" in data:
            raw_problem = data["problem"]
            
            # マップサイズを取得し、ディレクトリ名を決定 (例: "16x16")
            width = raw_problem["map"]["width"]
            height = raw_problem["map"]["height"]
            size_key = f"{width}x{height}"
            
            # 簡易サーバー向けの完全互換フォーマットへの変換
            formatted_config = {
                "problem": {
                    "width": width,
                    "height": height,
                    "cells": raw_problem["map"]["cells"],
                    "spots": raw_problem["spots"],
                    "agentStarts": raw_problem["agents"],
                    "fuelLimits": raw_problem["fuelLimits"],
                    "daySteps": raw_problem["daySteps"],
                    "daySeconds": raw_problem["daySeconds"],
                    "busyThreshold": raw_problem["busyThreshold"],
                    "jammedThreshold": raw_problem["jammedThreshold"]
                },
                "teams": [
                    {
                        "token": "nekomanma634",
                        "name": "BocchiAlgo"
                    }
                ]
            }
            
            # 初めて登場するマップサイズなら、ディレクトリを作成してカウンタを0で初期化
            if size_key not in counters:
                counters[size_key] = 0
                os.makedirs(os.path.join(BASE_OUTPUT_DIR, size_key), exist_ok=True)
            
            # ファイル名の決定 (0.json, 1.json, ...)
            file_index = counters[size_key]
            file_path = os.path.join(BASE_OUTPUT_DIR, size_key, f"{file_index}.json")
            
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(formatted_config, f, indent=4, ensure_ascii=False)
                
            print(f"  -> [成功] {size_key} フォルダの {file_index}.json に保存完了")
            
            # 次のファイルのためにカウントアップ
            counters[size_key] += 1
            
        else:
            print(f"  -> [スキップ] 'problem' データが見つかりません")
            
    except requests.exceptions.RequestException as e:
        print(f"  -> [エラー] 通信エラー: {e}")
    except KeyError as e:
        print(f"  -> [エラー] 必要なキーが見つかりません: {e}")
    except json.JSONDecodeError:
        print(f"  -> [エラー] JSONパース失敗")
        
    time.sleep(1.5)

print("すべての処理が完了しました。")
print("取得件数サマリー:")
for size, count in counters.items():
    print(f"  - {size}: {count}件")