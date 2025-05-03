import pandas as pd


class data_merger:
    def __init__(self, data1, data2):
        self.data1 = data1
        self.data2 = data2

    def data_merger_to_one(self):
        d1 = self.data1
        d2 = self.data2

        # Merge the two datasets on student_id, gender, and date_of_birth
        merged = pd.merge(d1, d2, on=['student_id', 'gender', 'date_of_birth'], how='outer')

        # Add enrollment status
        merged['Enrollment_status'] = merged['application_status'].apply(
            lambda x: 'Not Enrolled' if x != 'Active' else 'Enrolled'
        )

        # Load course data for CRICOS Code mapping
        try:
            c_data = pd.read_csv('course_data/course_data.csv', encoding='latin1', usecols=['Program Plan', 'CRICOS Code'])
        except Exception as e:
            print(f"Error reading course_data.csv: {e}")
            return merged  # Return merged anyway without CRICOS Code

        # Define function to map CRICOS code safely
        def get_cricos_code(x):
            row = c_data[c_data['Program Plan'] == x]
            if not row.empty:
                value = row['CRICOS Code'].values[0]
                return str(value).strip() if pd.notna(value) else None
            return None

        # Apply the mapping
        merged['cricos_code'] = merged['plan_code'].apply(get_cricos_code)

        # Filter out unwanted program codes
        merged = merged[~merged['program_code'].isin(['EXCHINPG', 'SAUGD', 'EL000', 'EXCHINUG'])]

        return merged
