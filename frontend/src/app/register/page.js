"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import axios from "axios";
import { Card, CardHeader, CardContent, CardFooter } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { motion } from "framer-motion";
import { ToastContainer, toast } from 'react-toastify';

export default function RegisterPage() {
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const router = useRouter();

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (password !== confirmPassword) {
      toast("Passwords do not match.");
      return;
    }
    try {
      const response = await axios.post(`${process.env.NEXT_PUBLIC_API_URL}/register`, {
        username,
        email,
        first_name:firstName,
        last_name:lastName,
        password,
      });
      if (response.status === 201) {
        const accessToken = response.data.accessToken;
        localStorage.setItem("accessToken", accessToken);
        router.push("/home");
      } else {
        toast("Registration failed. Please try again.");
      }
    } catch (error) {
      toast("An error occurred during registration. Please try again later.");
    }
  };

  return (
    <div className="relative min-h-screen flex items-center justify-center overflow-hidden">
      {/* Animated Gradient Background */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 1.5 }}
        className="absolute inset-0 bg-gradient-to-br from-green-400 via-blue-500 to-purple-600 animate-gradient"
      />

      {/* Glassmorphism Card with Responsive Margin */}
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ duration: 0.5, ease: "easeOut" }}
        className="relative z-10 w-full max-w-2xl mx-4 p-6 bg-white/10 backdrop-blur-lg rounded-2xl shadow-lg"
      >
        <Card>
          <CardHeader>
            <h1 className="text-2xl font-semibold text-center text-white">Register</h1>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              {/* First Name & Last Name in one row */}
              <div className="flex flex-col md:flex-row md:space-x-4">
                <div className="w-full">
                  <label htmlFor="firstName" className="block text-sm font-medium text-slate-600">
                    First Name:
                  </label>
                  <Input
                    type="text"
                    id="firstName"
                    value={firstName}
                    onChange={(e) => setFirstName(e.target.value)}
                    required
                    className="mt-1"
                  />
                </div>
                <div className="w-full">
                  <label htmlFor="lastName" className="block text-sm font-medium text-slate-600">
                    Last Name:
                  </label>
                  <Input
                    type="text"
                    id="lastName"
                    value={lastName}
                    onChange={(e) => setLastName(e.target.value)}
                    required
                    className="mt-1"
                  />
                </div>
              </div>

              {/* Username & Email in one row */}
              <div className="flex flex-col md:flex-row md:space-x-4">
                <div className="w-full">
                  <label htmlFor="username" className="block text-sm font-medium text-slate-600">
                    Username:
                  </label>
                  <Input
                    type="text"
                    id="username"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    required
                    className="mt-1"
                  />
                </div>
                <div className="w-full">
                  <label htmlFor="email" className="block text-sm font-medium text-slate-600">
                    Email:
                  </label>
                  <Input
                    type="email"
                    id="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    className="mt-1"
                  />
                </div>
              </div>

              {/* Password & Confirm Password in one row */}
              <div className="flex flex-col md:flex-row md:space-x-4">
                <div className="w-full">
                  <label htmlFor="password" className="block text-sm font-medium text-slate-600">
                    Password:
                  </label>
                  <Input
                    type="password"
                    id="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    className="mt-1"
                  />
                </div>
                <div className="w-full">
                  <label htmlFor="confirmPassword" className="block text-sm font-medium text-slate-600">
                    Confirm Password:
                  </label>
                  <Input
                    type="password"
                    id="confirmPassword"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    required
                    className="mt-1"
                  />
                </div>
              </div>

              <Button type="submit" className="w-full bg-green-600 hover:bg-green-700">
                Register
              </Button>
            </form>
          </CardContent>
          <CardFooter>
            <p className="text-sm text-slate-600 text-center">
              Already have an account?{" "}
              <a href="/login" className="text-blue-400 hover:underline">
                Login
              </a>
            </p>
          </CardFooter>
        </Card>
      </motion.div>

      {/* Background Animation CSS */}
      <style jsx>{`
        @keyframes gradient {
          0% {
            background-position: 0% 50%;
          }
          50% {
            background-position: 100% 50%;
          }
          100% {
            background-position: 0% 50%;
          }
        }
        .animate-gradient {
          background-size: 300% 300%;
          animation: gradient 10s ease infinite;
        }
      `}</style>
    </div>
  );
}
