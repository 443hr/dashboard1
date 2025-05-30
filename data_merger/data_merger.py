import pandas as pd

class data_merger:
    def __init__(self, data1, data2):
        self.data1 = data1
        self.data2 = data2

    def data_merger_to_one(self):
        d1 = self.data1
        d2 = self.data2

        # Merge main data on student details
        merged = pd.merge(d1, d2, on=['student_id'], how='outer')

        # Add enrollment status
        merged['Enrollment_status'] = merged['application_status'].apply(
            lambda x: 'Not Enrolled' if x != 'Active with EFTSL' else 'Enrolled'
        )

        # Load course data
        c_data = pd.read_csv('course_data/course_data.csv', encoding='latin1', usecols=['Program Plan', 'CRICOS Code'])

        # Ensure both plan columns are strings and clean
        merged['plan_code'] = merged['plan_code'].astype(str).str.strip()
        c_data['Program Plan'] = c_data['Program Plan'].astype(str).str.strip()

        # Merge to get CRICOS Code
        merged = pd.merge(merged, c_data, how='left', left_on='plan_code', right_on='Program Plan')
        merged.rename(columns={'CRICOS Code': 'cricos_code'}, inplace=True)
        merged.drop(columns=['Program Plan'], inplace=True)

        # Filter out specific program codes
        merged = merged[~merged['program_code'].isin(['EXCHINPG', 'SAUGD', 'EL000', 'EXCHINUG'])]

        return merged
