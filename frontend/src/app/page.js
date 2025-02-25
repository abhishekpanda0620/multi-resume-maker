"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";

const Page = () => {
  const router = useRouter();
  const isAuthenticated = false; // Replace with actual authentication logic

  useEffect(() => {
    if (isAuthenticated) {
      router.push("/home");
    } else {
      router.push("/login");
    }
  }, [isAuthenticated, router]);

  return null;
};

export default Page;
