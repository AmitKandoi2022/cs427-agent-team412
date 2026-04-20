package main

import (
	"context"
	"fmt"
	"os"
	"syscall"
	"github.com/containerd/fifo"
)

func main() {
	fn := "test_fifo"
	os.Remove(fn)
	
	// Create the named pipe
	err := syscall.Mkfifo(fn, 0666)
	if err != nil {
		fmt.Printf("Error creating fifo: %v\n", err)
		return
	}
	defer os.Remove(fn)

	// Attempt to open
	ctx := context.Background()
	f, err := fifo.OpenFifo(ctx, fn, syscall.O_RDONLY|syscall.O_NONBLOCK, 0666)
	
	if err != nil {
		fmt.Printf("OpenFifo returned error: %v\n", err)
	} else {
		fmt.Println("Successfully opened FIFO")
		f.Close()
	}
}