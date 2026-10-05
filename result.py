import os
import re
import glob
import subprocess

# ==========================================
# 実行環境設定
# ==========================================
CLIENT_EXE = "./app.exe"
BASE_DIR = "matches_json_categorized"
# ==========================================

def run_offline_match(problem_path):
    # problem_path が matches_json_categorized/16x16/0_1271.json の場合、
    # log_path を matches_json_categorized/16x16/0_1271.log に設定する
    log_path = os.path.splitext(problem_path)[0] + ".log"
    
    print(f"\n{'-'*40}")
    print(f"▶ 試合開始: {problem_path}")
    print(f"▶ ログ保存: {log_path}")
    
    # C++アルゴリズムを --offline 引数で直接起動
    client_args = [CLIENT_EXE, "--offline", problem_path]
    
    try:
        # C++の出力をUTF-8で取得
        result = subprocess.run(client_args, capture_output=True, text=True, encoding='utf-8', timeout=30)
        output = result.stdout if result.stdout else ""
        
        # 取得した出力（ログ）を .log ファイルに書き出し
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(output)
        
        # C++側で出力した最終スコアを正規表現で抽出
        kinds_match = re.search(r'種類数:\s*(\d+)', output)
        acc_match = re.search(r'種類数の累積:\s*(\d+)', output)
        balls_match = re.search(r'玉数:\s*(\d+)', output)
        
        print("【実行結果】")
        if kinds_match and acc_match and balls_match:
            print(f"  - 種類数       : {kinds_match.group(1)}")
            print(f"  - 種類数の累積 : {acc_match.group(1)}")
            print(f"  - 玉数         : {balls_match.group(1)}")
        else:
            print("  -> [警告] 結果を抽出できませんでした。")
            print(f"  -> 詳細は {log_path} を確認してください。")
            
    except subprocess.TimeoutExpired:
        print("  -> [エラー] 実行時間が超過しました。")
        # タイムアウト時もエラー情報をログに書き込む
        with open(log_path, "w", encoding="utf-8") as f:
            f.write("[ERROR] Timeout - 実行時間が30秒を超過しました\n")

def main():
    map_sizes = ["16x16", "24x24", "32x32"]
    for size in map_sizes:
        dir_path = os.path.join(BASE_DIR, size)
        if not os.path.exists(dir_path):
            continue
            
        print(f"\n\n{'='*40}")
        print(f" マップサイズ: {size} の検証を開始")
        print(f"{'='*40}")
        
        # フォルダ内の json ファイルを取得
        problem_files = glob.glob(os.path.join(dir_path, "*.json"))
        
        # "0_1271.json" の先頭の数値 "0" を基準にソートする処理
        def sort_by_index(filepath):
            basename = os.path.basename(filepath)
            index_part = basename.split('_')[0]
            try:
                return int(index_part)
            except ValueError:
                return 999999 # 万が一予期せぬファイル名があれば末尾に回す
                
        problem_files.sort(key=sort_by_index)
        
        for problem_path in problem_files:
            run_offline_match(problem_path)

if __name__ == "__main__":
    main()