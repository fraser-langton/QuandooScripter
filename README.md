# Quandoo Scripter
###### Developed by [Fraser Langton](https://github.com/fraser-langton) for Tennis Australia for integration between Archtics and Quandoo


## Getting started

### 1. Download Python
Download [Python](https://www.python.org/downloads/) (3.x) - https://www.python.org/downloads/

![alt text](https://i.ibb.co/ygr9F0c/Capture.png)


### 2. Download this repository
Either

[Download](https://github.com/fraser-langton/QuandooScripter/archive/master.zip) repository as a zip file:
![alt text](https://i.ibb.co/6wQHt2L/Screenshot-2021-03-05-111248.png)

Or clone the repository and use your IDE (for developers)


### 3. Configure integration
#### quandoo_merchants.json
Add the merchant-archtics pairs in the file _quandoo_merchants.json_, see example below:
```
{
    "merchant_id": "49293",
    "merchant_name": "Rockpool",
    "archtics_code": "DIRP",
    "reservation_tag": "Pre-Paid Package"
}
```
`merchant_id` - The Quandoo merchant id, this can be obtained from Quandoo representative or by looking in the URL 
in Business centre

`merchant_name`- Up to you, it is not critical

`archtics_code` - The **first 4 characters** of the archtics event name - **this must match the event names in _quandoo.csv_**

`reservation_tag` - The tag you want the bookings to have - **this must match a reservation tag from the business centre**

If you don't know how to edit JSON use [this editor](https://jsoneditoronline.org/) or do some research online


#### .env
Create a new _.env_ file (name it that exactly)
![alt text](https://i.ibb.co/mXzC7kj/Screenshot-2021-03-05-125447.png)
![alt text](https://i.ibb.co/nCDmKFt/Screenshot-2021-03-05-125518.png)
 
Open it (any text editor) and paste and replace the below with the authentication details you 
obtained from Quandoo 
```
AUTH_TOKEN=<auth_token>
AGENT_ID=<agent_id>
```
Save the file

### 4. Create a new venv environment and install dependencies
In the project directory (QuandooScripter-master) open a **PowerShell Window** 
![alt text](https://i.ibb.co/fn2QFd7/Screenshot-2021-03-05-135829.png)

Copy `python -m venv venv` and press Enter

Copy `venv\Scripts\pip install -r requirements.txt` and press Enter


## Running

### 1. Obtain latest quandoo report from archtics

### 2. Paste (and replace) new quandoo.csv

### 3. Run program
In the project directory (QuandooScripter-master) open a **PowerShell Window** 
![alt text](https://i.ibb.co/fn2QFd7/Screenshot-2021-03-05-135829.png)

Copy `venv\Scripts\python run.py` and press Enter


## FAQ

##### I want to add a new restaurant
See [Getting started - 3. Configure integration](#3-configure-integration), add an entry.   

##### I got a _QUANDOO_ERROR_
There might be something wrong with Quandoo or the way the merchant is configured on the business centre. If you can't figure out, you can try asking a Quandoo representative.

##### I got a _PROGRAM_ERROR_
Try to figure out what the error is saying and ensure the configuration is correct, if you can't sort it out [log an issue](https://github.com/fraser-langton/QuandooScripter/issues/new) - **copy and paste the full error** and _quandoo.csv_, _quandoo_bookings.json_, _quandoo_merchants.json_ **in a ZIP file** as per [example](https://github.com/fraser-langton/QuandooScripter/issues/1) and it can be addressed if a developer available.
