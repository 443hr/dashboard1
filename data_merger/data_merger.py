import pandas as pd


class data_merger:
    def __init__(self, data1,data2):
        self.data1 = data1
        self.data2 = data2
        


    def data_merger_to_one(self):
        d1 = self.data1
        d2 = self.data2
        
        merged = pd.merge(d1, d2, on=['student_id','gender','date_of_birth'], how='outer')
        merged['Enrollment_status'] = merged['application_status'].apply(
                lambda x: 'Not Enrolled' if x != 'Active' else 'Enrolled'
                                    )
        c_data = pd.read_csv('/Volumes/RMIT /project/course_data/course_data.csv', encoding='latin1', usecols=['Program Plan', 'CRICOS Code'])

        merged['cricos_code'] = merged['plan_code'].apply( lambda x: c_data[c_data['Program Plan'] == x]['CRICOS Code'].values[0] if x in c_data['Program Plan'].values else None)
        # Filter out rows where 'program_code' is in the specified list
        merged = merged[~merged['program_code'].isin(['EXCHINPG', 'SAUGD', 'EL000','EXCHINUG'])]


        return merged


       


    

        
        


