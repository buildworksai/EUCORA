// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
import { describe, it, expect } from 'vitest';
import { render, screen } from '@/test/utils';
import { useForm } from 'react-hook-form';
import {
  Form,
  FormField,
  FormItem,
  FormLabel,
  FormControl,
  FormDescription,
  FormMessage,
} from './form';
import { Input } from './input';

function TestForm() {
  const form = useForm({
    defaultValues: { name: '' },
  });

  return (
    <Form {...form}>
      <form>
        <FormField
          control={form.control}
          name="name"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Name</FormLabel>
              <FormControl>
                <Input {...field} />
              </FormControl>
              <FormDescription>Enter your name</FormDescription>
              <FormMessage />
            </FormItem>
          )}
        />
      </form>
    </Form>
  );
}

describe('Form Components', () => {
  it('renders form with all components', () => {
    render(<TestForm />);
    expect(screen.getByLabelText('Name')).toBeInTheDocument();
    expect(screen.getByText('Enter your name')).toBeInTheDocument();
  });

  it('displays error message when validation fails', () => {
    const TestFormWithError = () => {
      const form = useForm({
        defaultValues: { name: '' },
      });
      form.setError('name', { message: 'Name is required' });

      return (
        <Form {...form}>
          <FormField
            control={form.control}
            name="name"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Name</FormLabel>
                <FormControl>
                  <Input {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
        </Form>
      );
    };

    render(<TestFormWithError />);
    expect(screen.getByText('Name is required')).toBeInTheDocument();
  });
});
