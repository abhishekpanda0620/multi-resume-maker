"use client";
import { useEffect } from 'react';
import { useHistory } from 'react-router-dom';

const Page = () => {
  const history = useHistory();
  const isAuthenticated = false; // Replace with actual authentication logic

  useEffect(() => {
    if (isAuthenticated) {
      history.push('/home');
    } else {
      history.push('/login');
    }
  }, [isAuthenticated, history]);

  return null;
};

export default Page;