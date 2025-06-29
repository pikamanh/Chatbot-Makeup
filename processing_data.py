import pandas as pd
import os
import jsonlines
import csv

def merge_csv(csv_folder):
    # Tạo list để chứa dữ liệu từ các file
    dataframes = []

    for file in os.listdir(csv_folder):
        try:
            df = pd.read_csv(os.path.join(csv_folder, file))

            df = df.rename(columns= {
                df.columns[0]: 'Question',
                df.columns[1]: 'Answer'
            })

            dataframes.append(df)
        except Exception as e:
            print(f"Lỗi khi đọc {file}: {e}")

    # Gộp tất cả DataFrame lại
    combined_df = pd.concat(dataframes, ignore_index=True)

    # Lưu vào file CSV mới
    combined_df.to_csv('combined_output.csv', index=False)

    print("Đã gộp xong tất cả các file CSV!")

def preprocessing_data(file_data):
    df = pd.read_csv(file_data)
    for i, (question, answer) in df.iterrows():
        
        filtered_lst = answer.split('\n')
        # Loại bỏ phần tử rỗng
        filtered_lst = [s for s in filtered_lst if s.strip() != '']
        new_answer = '\n'.join(filtered_lst)
        new_answer = new_answer.replace("**", "")

        df.at[i, 'Answer'] = new_answer

    df.to_csv(file_data, index=False)

def format_json(file_json):
    output = 'output.json'
    
    with open(output, 'w', encoding='utf-8') as output_file:
        json_writer = jsonlines.Writer(output_file)

        with open(file_json, 'r', encoding='utf-8') as input_file:
            json_reader = jsonlines.Reader(input_file)

            entries = json_reader.read()
            for entry in entries:
                format_text = f"<s>[INST] {entry['Question']} [/INST] {entry['Answer']} </s>"

                json_writer.write({'text': format_text})

    print("Successfully.")

def format_csv_to_jsonl(file_csv):
    output = 'train.jsonl'  # đúng định dạng jsonlines

    with open(output, 'w', encoding='utf-8') as output_file:
        json_writer = jsonlines.Writer(output_file)

        with open(file_csv, 'r', encoding='utf-8') as input_file:
            csv_reader = csv.DictReader(input_file)

            for row in csv_reader:
                format_text = f"<s>[INST] {row['Question']} [/INST] {row['Answer']} </s>"
                json_writer.write({'text': format_text})

    print("✅ Successfully converted to JSONL.")

def split_question(file_question):
    questions = pd.read_csv(file_question)

    # Tính tổng số hàng và số lượng mỗi phần
    total = len(questions)
    n = 3
    chunk_size = total // n

    # Chia đều và lưu từng phần
    for i in range(n):
        start = i * chunk_size
        # Phần cuối cùng lấy đến hết
        end = (i + 1) * chunk_size if i != n - 1 else total
        part = questions.iloc[start:end]
        part.to_csv(f'questions_part_{i+1}.csv', index=False)

if __name__ == '__main__':
    # merge_csv('merge')
    # preprocessing_data('combined_output.csv')
    format_csv_to_jsonl('combined_output.csv')