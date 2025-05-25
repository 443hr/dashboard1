# data_cleaner.py
import pandas as pd

class data_cleaner:
    def __init__(self, l1, l2):
        self.l1 = l1
        self.l2 = l2

    def data_cleaner_fun(self):
        d1 = pd.read_excel(self.l1)
        d2 = pd.read_excel(self.l2)
        
        column_drop = [
            "ProviderArrangedHealthCover (OSHC)", "OSHC Start Date", "OSHC End Date", "OSHC Provider",
            "English Test Exemption Reason", "English Test Type", "English Test Score", "English Test Date",
            "Other Form Of Testing", "Other Form Of Testing Comments", "Is Dual Qualification",
            "Narrow Field Of Education 1", "Detailed Field Of Education 1", "Broad Field Of Education 2",
            "Narrow Field Of Education 2", "Detailed Field Of Education 2", "Foundation Studies",
            "Work Component", "Work Component Hrs/ Wk", "Work Component Weeks", "Work Component Total Hours",
            "Course Language", "Duration In Weeks", "Current Total Course Fee", "Immigration Post",
            "Email Address", "Mobile", "Phone", "Student Address Line 1", "Student Address Line 2",
            "Student Address Line 3", "Student Address Line 4", "Student Address Locality",
            "Student Address State", "Student Address Country", "Student Address Post Code","applicant_id"
        ]

        # Drop columns only if they exist
        d1 = d1.drop(columns=[col for col in column_drop if col in d1.columns], errors='ignore')
        d2 = d2.drop(columns=[col for col in column_drop if col in d2.columns], errors='ignore')

        # Rename columns for consistency
        d1.rename(columns={'Provider Student ID': 'student_id', 'Gender': 'gender', 'Date Of Birth': 'date_of_birth'}, inplace=True)
        d2.rename(columns={'rmit_student_id': 'student_id'}, inplace=True)

        # Reorder columns to keep 'student_id' first
        d1 = d1[['student_id'] + [col for col in d1.columns if col != 'student_id']]
        d2 = d2[['student_id'] + [col for col in d2.columns if col != 'student_id']]

        # Standardize gender labels
        d1['gender'] = d1['gender'].apply(lambda x: 'Male' if x == 'MALE' else 'Female')
        d2['gender'] = d2['gender'].apply(lambda x: 'Male' if x == 'M' else 'Female')

        
        date_cols = ['date_of_birth','Proposed Start Date', 'Proposed End Date','Actual Start Date', 'Visa Non Grant Action Date'
                     ,'Visa Effective Date','Visa End Date','COE Created Date','COE Last Updated','Welfare Start Date',
                     'Welfare End Date','created_date','commencement_date'
                             ]
        for col in date_cols:
            if col in d1.columns:
                d1[col] = pd.to_datetime(d1[col], errors='coerce').dt.strftime('%d/%m/%Y')
            if col in d2.columns:
                d2[col] = pd.to_datetime(d2[col], errors='coerce').dt.strftime('%d/%m/%Y')

        

        return d1, d2
