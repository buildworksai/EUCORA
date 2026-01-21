// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
/**
 * Login page with session-based email/password authentication.
 */
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useAuthStore } from '@/lib/stores/authStore';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from '@/components/ui/card';
import { ThemeProvider } from '@/components/layout/ThemeProvider';
import { Eye, EyeOff, Lock, Mail, AlertCircle, Loader2, Sparkles } from 'lucide-react';

const loginSchema = z.object({
  email: z.string().email('Please enter a valid email address'),
  password: z.string().min(1, 'Password is required'),
  rememberMe: z.boolean().optional(),
});

type LoginFormData = z.infer<typeof loginSchema>;

export default function Login() {
  const navigate = useNavigate();
  const { login, isAuthenticated, isLoading, error, clearError } = useAuthStore();
  const [showPassword, setShowPassword] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
    setValue,
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: '',
      password: '',
      rememberMe: false,
    },
  });

  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated) {
      navigate('/dashboard');
    }
  }, [isAuthenticated, navigate]);

  // Clear errors on unmount
  useEffect(() => {
    return () => clearError();
  }, [clearError]);

  const onSubmit = async (data: LoginFormData) => {
    const success = await login({
      email: data.email,
      password: data.password,
      rememberMe: data.rememberMe,
    });
    
    if (success) {
      navigate('/dashboard');
    }
  };

  const fillDemoCredentials = () => {
    setValue('email', 'demo@eucora.com');
    setValue('password', 'admin@134');
  };

  const fillAdminCredentials = () => {
    setValue('email', 'admin@eucora.com');
    setValue('password', 'admin@134');
  };

  return (
    <ThemeProvider>
      <div className="relative min-h-screen flex items-center justify-center overflow-hidden bg-[#0a0f1a]">
        {/* Animated Background */}
        <div className="absolute inset-0 z-0">
          {/* Gradient base */}
          <div className="absolute inset-0 bg-gradient-to-br from-[#0d1526] via-[#0a0f1a] to-[#060a12]" />
          
          {/* Animated orbs */}
          <div className="absolute top-1/4 -left-20 w-96 h-96 bg-eucora-deepBlue/20 rounded-full blur-3xl animate-pulse-slow" />
          <div className="absolute bottom-1/4 -right-20 w-80 h-80 bg-eucora-teal/15 rounded-full blur-3xl animate-pulse-slow" style={{ animationDelay: '1s' }} />
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-eucora-deepBlue/5 rounded-full blur-3xl" />
          
          {/* Grid pattern overlay */}
          <div 
            className="absolute inset-0 opacity-[0.03]"
            style={{
              backgroundImage: `
                linear-gradient(to right, rgba(255,255,255,0.1) 1px, transparent 1px),
                linear-gradient(to bottom, rgba(255,255,255,0.1) 1px, transparent 1px)
              `,
              backgroundSize: '60px 60px',
            }}
          />
          
          {/* Floating particles */}
          <div className="absolute top-20 left-1/4 w-2 h-2 bg-eucora-teal/40 rounded-full animate-bounce" style={{ animationDuration: '3s' }} />
          <div className="absolute top-40 right-1/3 w-1.5 h-1.5 bg-eucora-gold/30 rounded-full animate-bounce" style={{ animationDuration: '4s', animationDelay: '0.5s' }} />
          <div className="absolute bottom-32 left-1/3 w-2 h-2 bg-eucora-deepBlue/40 rounded-full animate-bounce" style={{ animationDuration: '3.5s', animationDelay: '1s' }} />
        </div>

        {/* Login Card */}
        <div className="relative z-10 w-full max-w-md p-4 transition-all duration-700 opacity-100 translate-y-0">
          <Card className="border border-white/10 shadow-2xl bg-[#0d1526]/90 backdrop-blur-xl">
            <CardHeader className="text-center pb-2 space-y-4">
              {/* Logo */}
              <div className="flex justify-center">
                <div className="relative group">
                  <div className="absolute inset-0 bg-gradient-to-r from-eucora-deepBlue to-eucora-teal rounded-2xl blur-xl opacity-50 group-hover:opacity-75 transition-opacity" />
                  <div className="relative p-4 rounded-2xl bg-gradient-to-br from-eucora-deepBlue to-eucora-deepBlue-dark shadow-lg">
                    <img src="/logo.png" alt="EUCORA Logo" className="w-14 h-14 object-contain" />
                  </div>
                </div>
              </div>
              
              {/* Title */}
              <div className="space-y-2">
                <CardTitle className="text-3xl font-bold tracking-tight text-white">
                  Welcome Back
                </CardTitle>
                <CardDescription className="text-gray-400">
                  Sign in to EUCORA Control Plane
                </CardDescription>
              </div>
            </CardHeader>

            <CardContent className="space-y-6 pt-4">
              {/* Error Alert */}
              {error && (
                <div className="flex items-center gap-3 p-4 text-sm text-red-400 bg-red-500/10 rounded-lg border border-red-500/20 animate-fade-in">
                  <AlertCircle className="h-5 w-5 flex-shrink-0" />
                  <span>{error}</span>
                </div>
              )}

              <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
                {/* Email Field */}
                <div className="space-y-2">
                  <Label htmlFor="email" className="text-sm font-medium text-gray-300">
                    Email Address
                  </Label>
                  <div className="relative group">
                    <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-500 group-focus-within:text-eucora-teal transition-colors" />
                    <Input
                      id="email"
                      type="email"
                      placeholder="you@eucora.com"
                      className="pl-11 h-12 bg-white/5 border-white/10 text-white placeholder:text-gray-500 focus:border-eucora-teal focus:ring-eucora-teal/20 transition-all"
                      {...register('email')}
                    />
                  </div>
                  {errors.email && (
                    <p className="text-sm text-red-400 mt-1">{errors.email.message}</p>
                  )}
                </div>

                {/* Password Field */}
                <div className="space-y-2">
                  <Label htmlFor="password" className="text-sm font-medium text-gray-300">
                    Password
                  </Label>
                  <div className="relative group">
                    <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-500 group-focus-within:text-eucora-teal transition-colors" />
                    <Input
                      id="password"
                      type={showPassword ? 'text' : 'password'}
                      placeholder="••••••••"
                      className="pl-11 pr-11 h-12 bg-white/5 border-white/10 text-white placeholder:text-gray-500 focus:border-eucora-teal focus:ring-eucora-teal/20 transition-all"
                      {...register('password')}
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3.5 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300 transition-colors"
                    >
                      {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                    </button>
                  </div>
                  {errors.password && (
                    <p className="text-sm text-red-400 mt-1">{errors.password.message}</p>
                  )}
                </div>

                {/* Remember Me */}
                <div className="flex items-center justify-between">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      className="w-4 h-4 rounded border-white/20 bg-white/5 text-eucora-teal focus:ring-eucora-teal/20"
                      {...register('rememberMe')}
                    />
                    <span className="text-sm text-gray-400">Remember me</span>
                  </label>
                </div>

                {/* Submit Button */}
                <Button
                  type="submit"
                  disabled={isLoading}
                  className="w-full h-12 text-base font-semibold bg-gradient-to-r from-eucora-deepBlue to-eucora-deepBlue-dark hover:from-eucora-deepBlue-dark hover:to-eucora-deepBlue text-white shadow-lg shadow-eucora-deepBlue/25 hover:shadow-xl hover:shadow-eucora-deepBlue/30 transition-all duration-300"
                >
                  {isLoading ? (
                    <>
                      <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                      Signing in...
                    </>
                  ) : (
                    'Sign In'
                  )}
                </Button>
              </form>

              {/* Quick Access Buttons */}
              <div className="relative">
                <div className="absolute inset-0 flex items-center">
                  <span className="w-full border-t border-white/10" />
                </div>
                <div className="relative flex justify-center text-xs uppercase">
                  <span className="bg-[#0d1526] px-3 text-gray-500">Quick Access</span>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <Button
                  type="button"
                  variant="outline"
                  onClick={fillDemoCredentials}
                  className="h-11 border-white/10 bg-white/5 text-gray-300 hover:bg-eucora-teal/10 hover:border-eucora-teal/30 hover:text-eucora-teal transition-all"
                >
                  <Sparkles className="mr-2 h-4 w-4" />
                  Demo User
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  onClick={fillAdminCredentials}
                  className="h-11 border-white/10 bg-white/5 text-gray-300 hover:bg-eucora-gold/10 hover:border-eucora-gold/30 hover:text-eucora-gold transition-all"
                >
                  <Lock className="mr-2 h-4 w-4" />
                  Admin
                </Button>
              </div>
            </CardContent>

            <CardFooter className="flex flex-col gap-4 text-center text-xs text-gray-500 pt-2 pb-6">
              <div className="space-y-1">
                <p>
                  Protected by enterprise security policies
                </p>
                <p className="text-gray-600">
                  All sessions are monitored and logged
                </p>
              </div>
              <div className="flex items-center justify-center gap-2 text-gray-600">
                <span>Built by BuildWorks.AI</span>
                <span>•</span>
                <span>v1.0.0</span>
              </div>
            </CardFooter>
          </Card>

          {/* Credential Hints */}
          <div className="mt-4 p-4 rounded-lg bg-eucora-teal/5 border border-eucora-teal/20" style={{ transitionDelay: '300ms' }}>
            <p className="text-xs text-eucora-teal font-medium mb-2">Demo Credentials</p>
            <div className="grid grid-cols-2 gap-4 text-xs text-gray-400">
              <div>
                <p className="font-medium text-gray-300">Admin Access</p>
                <p>admin@eucora.com</p>
                <p>admin@134</p>
              </div>
              <div>
                <p className="font-medium text-gray-300">Demo Access</p>
                <p>demo@eucora.com</p>
                <p>admin@134</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </ThemeProvider>
  );
}
