Code for define parameters by terminal :
py
    model = CityModel(
    num_humans=5,
    num_tourists=8,
    num_model_citizens=2,
    street_cleaner_capacity=3,
    park_cleaner_capacity=2,
    bin_transporter_capacity=5,
    container_transporter_capacity=10,
    model_citizen_capacity=4,
)


Code to run simulation if connection issue
    1. netstat -ano | findstr :8766  
    2. taskkill /PID xxxx /F 
    3. solara run model/CityModel.py --port 876x