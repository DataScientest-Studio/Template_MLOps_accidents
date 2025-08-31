import pandas as pd
from sklearn.preprocessing import LabelEncoder

def clean_file(input_path, output_path):
    df = pd.read_csv(input_path, encoding='utf-8', sep=',', low_memory=False)

    for col in df.columns:
        if df[col].dtype == 'object':
            df[col] = df[col].astype(str).str.replace('\xa0', '', regex=False).str.replace('Â', '', regex=False).str.strip()
            try:
                df[col] = pd.to_numeric(df[col])
            except:
                encoder = LabelEncoder()
                df[col] = encoder.fit_transform(df[col].astype(str))

    df.to_csv(output_path, index=False)

clean_file('data/preprocessed/X_train.csv', 'data/preprocessed/X_train_clean.csv')
clean_file('data/preprocessed/X_test.csv', 'data/preprocessed/X_test_clean.csv')
