import requests

# Define API parameters

def get_google_distance(origin, destination):
    api_key = "AIzaSyCJfMkDFON8NPSF-yDwye5nHt_2ZExcEDE"

    # Format the API request
    base_url = "https://maps.googleapis.com/maps/api/distancematrix/json"
    params = {
        "origins": origin,
        "destinations": destination,
        "key": api_key
    }

    # Make the request
    response = requests.get(base_url, params=params)
    data = response.json()

    # Print the result
    if response.status_code == 200:
        try:
            distance = data["rows"][0]["elements"][0]["distance"]["text"]
            duration = data["rows"][0]["elements"][0]["duration"]["text"]
            return(distance,duration)
        except KeyError:
            return(None)
    else:
        return(None)