from data_cleaner.data_cleaner import data_cleaner
from data_merger.data_merger import data_merger  # assuming similar structure there

l1 = "/Volumes/RMIT /project/data/PRISMS/prisms.xlsx"
l2 = "/Volumes/RMIT /project/data/PRISMS/air.xlsx"

d_clean = data_cleaner(l1, l2)
d1, d2 = d_clean.data_cleaner_fun()

um_data = data_merger(d1, d2)
m_data = um_data.data_merger_to_one()

m_data.to_excel('/Volumes/RMIT /project/data/PRISMS/merged.xlsx', index=False)
print("Data merging process is successful!!!")
