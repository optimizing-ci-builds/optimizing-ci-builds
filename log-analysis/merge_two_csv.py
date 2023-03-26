import sys
import pandas as pd

result_csv_with_instrumentation=sys.argv[1]
result_csv_without_instrumentation=sys.argv[2]

a = pd.read_csv(result_csv_with_instrumentation)
b = pd.read_csv(result_csv_without_instrumentation)
#b = b.dropna(axis=1)
merged = pd.merge(b, a, on=None)

#merged.to_csv("output_1.csv", index=False)
#print(merged)
merged.to_csv(sys.argv[3])
#files = os.path.join(result_csv_with_instrumentation, result_csv_without_instrumentation)

