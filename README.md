# multi-resume-maker

## Overview

multi-resume-maker is an AI-powered tool that allows users to create job-specific resumes by uploading a master resume and job descriptions (JDs). The tool uses AI to modify the master resume to match the job requirements, making it highly relevant and tailored.

## Features

- AI-powered resume customization
- Upload master resume and job descriptions
- Multiple resume templates
- Easy to use interface
- Customizable sections
- Export to PDF and other formats

## Installation

To install multi-resume-maker, clone the repository and install the dependencies for both frontend and backend:

```bash
git clone https://github.com/yourusername/multi-resume-maker.git
cd multi-resume-maker
```

### Frontend

```bash
cd frontend
npm install
```

### Backend

It is recommended to use a virtual environment for the backend. You can create and activate a virtual environment using the following commands:

```bash
cd ../backend
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
pip install -r requirements.txt
python manage.py migrate
```

## Usage

To start the application, run the following commands in separate terminals:

### Frontend

```bash
cd frontend
npm start
```

### Backend

```bash
cd backend
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
python manage.py runserver
```

Then open your browser and navigate to `http://localhost:3000`.

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request.

## License

This project is licensed under the MIT License.