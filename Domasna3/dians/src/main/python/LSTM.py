import pandas as pd
# import seaborn as sns
# import matplotlib.pyplot as plt
import datetime
import numpy as np
import json
from datetime import datetime
from keras.api.models import Sequential
from keras.api.layers import Dense, Dropout, LSTM, Input
from keras.api.callbacks import EarlyStopping
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import confusion_matrix, r2_score, mean_squared_error, mean_absolute_error
import os

mega_data_path = './Smestuvanje/mega-data.csv'
processed_dataset_path = './Smestuvanje/processed_lstm.csv'
names_json_filepath = './Smestuvanje/names.json'
codes_json_filepath = './Smestuvanje/processed_codes.json'


def predict_values_for_issuer(all_data: pd.DataFrame, issuer_code: str):
    issuer_table_data = all_data[all_data['code'] == issuer_code]

    if len(issuer_table_data) < 100:
        return

    issuer_table_data = issuer_table_data.drop_duplicates(subset=['date'])
    issuer_table_data['Moving average'] = issuer_table_data['close'].rolling(window=3, min_periods=1).mean()
    issuer_table_data['EMA'] = issuer_table_data['close'].ewm(span=5, adjust=False).mean()
    issuer_table_data.dropna(axis=0, inplace=True)
    issuer_table_data.set_index('date', inplace=True)
    issuer_table_data = issuer_table_data.drop \
        (columns=['code', 'max', 'low', 'avg', 'volume', 'turnover in BEST', 'total turnover'])

    calc_lag = round(len(issuer_table_data) / 500.0)
    if calc_lag > 3:
        lag = calc_lag
    else:
        lag = 2
    periods = []
    for i in range(lag, 0, -1):
        periods.append(i)

    merged = pd.concat([issuer_table_data, issuer_table_data.shift(periods=periods)], axis=1)
    merged = merged.dropna(axis=0)
    og_cols = ['close', 'Moving average', 'EMA']
    features = [feature for feature in merged.columns if feature not in og_cols]

    X = merged[features]
    Y = merged['close']
    x_train, x_test, y_train, y_test = train_test_split(X, Y, test_size=0.3, shuffle=False)

    scaler = MinMaxScaler()
    x_train = scaler.fit_transform(x_train)
    x_test = scaler.transform(x_test)
    x_train = x_train.reshape((x_train.shape[0], lag, len(features) // lag))
    x_test = x_test.reshape((x_test.shape[0], lag, len(features) // lag))

    model = Sequential([
        Input((x_train.shape[1], x_train.shape[2],)),
        LSTM(64, activation="relu", return_sequences=True),
        LSTM(32, activation="relu"),
        Dense(1, activation="linear")
    ])
    model.compile(
        loss="mean_squared_error",
        optimizer="adam",
        metrics=["mean_squared_error"], )

    early_stop = EarlyStopping(
        patience=6, monitor='val_loss', restore_best_weights=True)

    history = model.fit(x_train, y_train, batch_size=16, epochs=32, shuffle=False, validation_split=0.1,
                        callbacks=[early_stop], verbose=0)

    y_pred = model.predict(x_test)

    score = r2_score(y_test, y_pred)

    merged_res = pd.concat([y_test.reset_index(), pd.DataFrame({"close_pred": y_pred.flatten()})], axis=1)
    merged_res['date'] = merged_res['date'].dt.strftime('%d.%m.%Y')

    merged_res['code'] = [issuer_code] * len(merged_res)
    merged_res['score'] = [score] * len(merged_res)
    merged_res['date_processed'] = [datetime.today().date().isoformat()] * len(merged_res)

    return merged_res


def save_processed_codes_to_json(codes_list: list, json_codes_path: str):
    with open(json_codes_path, 'w', encoding='utf-8') as f:
        json.dump(codes_list, f, ensure_ascii=False, indent=4)
        print(f"Processed issuer codes saved to {json_codes_path}")


def process_all():
    data = pd.read_csv(mega_data_path)
    data['date'] = pd.to_datetime(data['date'], format='%d.%m.%Y')
    data.sort_values('date', inplace=True)

    json_data = find_last_processing(names_json_filepath, processed_dataset_path)
    if not json_data:
        print("No issuers to process or data already up-to-date.")
        return

    all_predicts = []
    all_predict_codes = []

    # Process each issuer
    for issuer in json_data:
        try:
            issuer_dict = predict_values_for_issuer(data, issuer['Issuer code'])
            if issuer_dict is not None:
                all_predicts.append(issuer_dict)
                all_predict_codes.append(issuer['Issuer code'])
        except Exception as e:
            print(f"Error processing issuer {issuer['Issuer code']}: {e}")

    # Save the results
    if all_predicts:
        try:
            concatenated_data = pd.concat(all_predicts)
            concatenated_data.to_csv(processed_dataset_path, index=False)
            save_processed_codes_to_json(all_predict_codes, codes_json_filepath)
            print(f"Processed data saved to {processed_dataset_path}")
        except Exception as e:
            print(f"Error saving processed data: {e}")
    else:
        print("No data to save.")


def find_last_processing(names_file_path: str, processed_path: str):
    with open(names_file_path, 'r', encoding='utf-8') as file_og:
        # Load the contents of the JSON file into a Python list of dictionaries
        json_data = json.load(file_og)

    # Initialize an empty list for processed_data
    processed_data = None

    # Check if the processed file exists
    if os.path.exists(processed_path):
        # If the file exists, load the processed issuers data
        processed_data = pd.read_csv(processed_path)

    # Get today's date in the same format as the 'last_date' (ISO 8601)
    today_date = datetime.today().date().isoformat()

    if processed_data is not None:
        last_processed_date = processed_data.iloc[0]['date_processed']

        if last_processed_date == today_date:
            return

    return json_data


process_all()