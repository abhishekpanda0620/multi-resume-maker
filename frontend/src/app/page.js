"use client";

import { useState } from "react";
import axios from "axios";
import Image from "next/image";
import { Document, Page, pdfjs } from 'react-pdf';

// Set up PDF.js worker
pdfjs.GlobalWorkerOptions.workerSrc = '/pdf.worker.min.mjs';

export default function Home() {
  const [masterResume, setMasterResume] = useState(null);
  const [jobDescription, setJobDescription] = useState("");
  const [customizedResumeLink, setCustomizedResumeLink] = useState("");
  const [pdfUrl, setPdfUrl] = useState(null);
  const [numPages, setNumPages] = useState(null);
  const [pageNumber, setPageNumber] = useState(1);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  function onDocumentLoadSuccess({ numPages }) {
    setNumPages(numPages);
    setIsLoading(false);
  }

  function onDocumentLoadError(error) {
  }

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    setMasterResume(file);
    if (file) {
      setIsLoading(true);
      const fileUrl = URL.createObjectURL(file);
      setPdfUrl(fileUrl);
    }
  };

  const handleInputChange = (e) => {
    setJobDescription(e.target.value);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    setCustomizedResumeLink(null);
  
    const formData = new FormData();
    formData.append("master_resume", masterResume);
    formData.append("job_description", jobDescription);
  
    try {
      const response = await axios.post(
        "http://localhost:8000/api/customized-resumes/customize/",
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data",
          },
          // Add timeout and response type
          timeout: 30000,
          responseType: 'json',
        }
      );
  
      if (response.data && response.data.customized_resume_file) {
        setCustomizedResumeLink(response.data.customized_resume_file);
      } else {
        throw new Error('Invalid response format from server');
      }
    } catch (error) {
      console.error('Error customizing resume:', error);
      setError(
        error.response?.data?.message || 
        error.message || 
        'An error occurred while customizing your resume'
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gradient-to-r from-blue-500 to-purple-600 text-white p-4 md:p-8">
      <div className="flex flex-col lg:flex-row gap-4 lg:gap-8 w-full max-w-6xl">
        <main className="bg-white text-black p-4 md:p-8 rounded-lg shadow-lg w-full lg:w-2/5">
          <h1 className="text-2xl md:text-4xl font-bold mb-6 md:mb-8 text-center">Multi-Resume Maker</h1>
          <form className="flex flex-col gap-4" onSubmit={handleSubmit}>
            <div className="relative">
              <label className="block mb-2 text-lg font-medium">Upload Master Resume:</label>
              <input
                type="file"
                accept=".pdf"
                onChange={handleFileChange}
                required
                className="block w-full text-sm text-gray-900 border-2 border-dashed border-gray-300 rounded-lg cursor-pointer bg-gray-50 focus:outline-none p-4 hover:border-blue-500 transition-colors"
              />
              <div className="text-center text-sm text-gray-500 mt-2">
                Drag and drop your PDF here or click to browse
              </div>
            </div>
            <div>
              <label className="block mb-2 text-lg font-medium">Enter Job Description:</label>
              <textarea
                value={jobDescription}
                onChange={handleInputChange}
                required
                placeholder="Paste the job description here..."
                className="block w-full text-sm text-gray-900 border border-gray-300 rounded-lg bg-gray-50 focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none h-48 p-4 resize-none"
              />
            </div>
            {error && (
  <div className="p-4 mb-4 text-sm text-red-800 rounded-lg bg-red-50" role="alert">
    <span className="font-medium">Error!</span> {error}
  </div>
)}

<button
  type="submit"
  disabled={isSubmitting}
  className={`mt-4 w-full py-3 px-4 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg transition-all transform 
    ${isSubmitting 
      ? 'opacity-75 cursor-not-allowed' 
      : 'hover:from-blue-700 hover:to-purple-700 hover:scale-105 focus:ring-2 focus:ring-offset-2 focus:ring-blue-500'
    }`}
>
  {isSubmitting ? (
    <div className="flex items-center justify-center">
      <div className="w-5 h-5 border-t-2 border-b-2 border-white rounded-full animate-spin mr-2"></div>
      Processing...
    </div>
  ) : (
    'Customize Resume'
  )}
</button>
          </form>
          {customizedResumeLink && (
  <div className="mt-6 text-center p-4 bg-green-50 rounded-lg">
    <div className="mb-2 text-green-800">Resume customized successfully!</div>
    <a
      href={customizedResumeLink}
      target="_blank"
      rel="noopener noreferrer"
      className="inline-flex items-center gap-2 text-green-600 hover:text-green-800 font-medium"
    >
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
      </svg>
      Download Customized Resume
    </a>
  </div>
)}
        </main>

        {pdfUrl && (
          <div className="bg-white rounded-lg shadow-lg p-4 w-full lg:w-3/5">
            <h2 className="text-xl font-semibold mb-4 text-black">PDF Preview</h2>
            <div className="h-[500px] md:h-[600px] lg:h-[800px] overflow-auto relative">
              {isLoading && (
                <div className="absolute inset-0 flex items-center justify-center bg-gray-50">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
                </div>
              )}
              <Document
                file={pdfUrl}
                onLoadSuccess={onDocumentLoadSuccess}
                onLoadError={onDocumentLoadError}
                loading={
                  <div className="flex items-center justify-center h-full">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
                  </div>
                }
                className="border border-gray-200 rounded"
              >
                {Array.from(new Array(numPages), (el, index) => (
                  <Page
                    key={`page_${index + 1}`}
                    pageNumber={index + 1}
                    className="max-w-full mb-4"
                    width={Math.min(window.innerWidth * 0.9, 600)}
                    renderTextLayer={false}
                    renderAnnotationLayer={false}
                  />
                ))}
              </Document>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
