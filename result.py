import os
import re
import glob
import json
import time
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed

# ==========================================
# 実行環境設定
# ==========================================
CLIENT_EXE = "./app.exe"
BASE_DIR = "matches_json_categorized"

# 同時に実行するプロセス数（お使いのPCのCPUコア数に合わせて調整してください）
MAX_WORKERS = 4 

# JSONの設定時間（全日数の合計）に加算する猶予時間（初期化処理などを考慮）
MARGIN_SEC = 10 
# ==========================================

def run_offline_match(problem_path):
    log_path = os.path.splitext(problem_path)[0] + ".log"
    out_buf = []
    out_buf.append(f"\n{'-'*40}")
    
    # 1. JSONファイルを読み込んで制限時間を計算
    timeout_limit = 30 # デフォルト
    try:
        with open(problem_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # ルートに展開されていることを想定
            day_seconds = data.get('daySeconds', [])
            if day_seconds:
                timeout_limit = sum(day_seconds) + MARGIN_SEC
    except Exception as e:
        out_buf.append(f"  -> [警告] JSONの読み込みに失敗したためデフォルトの30秒を使用します: {e}")

    out_buf.append(f"▶ 試合開始: {problem_path} (許容実行時間: {timeout_limit}秒)")
    out_buf.append(f"▶ ログ保存: {log_path}")
    
    client_args = [CLIENT_EXE, "--offline", problem_path]
    
    start_time = time.time()
    
    try:
        # 計算した timeout_limit を適用
        result = subprocess.run(client_args, capture_output=True, text=True, encoding='utf-8', timeout=timeout_limit)
        output = result.stdout if result.stdout else ""
        
        elapsed_time = time.time() - start_time
        
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(output)
        
        kinds_match = re.search(r'種類数:\s*(\d+)', output)
        acc_match = re.search(r'種類数の累積:\s*(\d+)', output)
        balls_match = re.search(r'玉数:\s*(\d+)', output)
        
        out_buf.append("【実行結果】")
        if kinds_match and acc_match and balls_match:
            out_buf.append(f"  - 種類数       : {kinds_match.group(1)}")
            out_buf.append(f"  - 種類数の累積 : {acc_match.group(1)}")
            out_buf.append(f"  - 玉数         : {balls_match.group(1)}")
            out_buf.append(f"  - 実行時間     : {elapsed_time:.3f} 秒")
        else:
            out_buf.append("  -> [警告] 結果を抽出できませんでした。")
            out_buf.append(f"  -> 詳細は {log_path} を確認してください。")
            
    except subprocess.TimeoutExpired:
        out_buf.append(f"  -> [エラー] 実行時間が{timeout_limit}秒を超過しました。")
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(f"[ERROR] Timeout - 実行時間が{timeout_limit}秒を超過しました\n")
            
    # コンソールの出力が他スレッドと混ざらないように、改行で繋いで一括で返す
    return "\n".join(out_buf)

def main():
    map_sizes = ["16x16"]
    # map_sizes = ["24x24"]
    # map_sizes = ["32x32"]
    
    for size in map_sizes:
        dir_path = os.path.join(BASE_DIR, size)
        if not os.path.exists(dir_path):
            continue
            
        print(f"\n\n{'='*40}")
        print(f" マップサイズ: {size} の検証を開始 (並列実行数: {MAX_WORKERS})")
        print(f"{'='*40}")
        
        problem_files = glob.glob(os.path.join(dir_path, "*.json"))
        
        def sort_by_index(filepath):
            basename = os.path.basename(filepath)
            index_part = basename.split('_')[0]
            try:
                return int(index_part)
            except ValueError:
                return 999999
                
        problem_files.sort(key=sort_by_index)
        
        # ThreadPoolExecutor を使用して並列処理
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            # タスクを投入
            future_to_path = {executor.submit(run_offline_match, path): path for path in problem_files}
            
            # 完了したものから順次結果を表示
            for future in as_completed(future_to_path):
                try:
                    result_output = future.result()
                    print(result_output)
                except Exception as exc:
                    path = future_to_path[future]
                    print(f"\n{'-'*40}\n▶ 試合開始: {path}\n  -> [致命的なエラー] 例外が発生しました: {exc}")

if __name__ == "__main__":
    main()