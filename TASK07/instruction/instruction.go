package instruction

import "fmt"

type Instruction interface {
	Instruction() string
	MemOffset() int
}

type Value struct {
	X      byte
	Offset int
}

func (v Value) Instruction() string {
	return fmt.Sprintf("Change Value at %d by %d", v.Offset, int8(v.X))
}

func (v Value) MemOffset() int {
	return v.Offset
}

type Input struct {
	Offset int
}

func (i Input) Instruction() string {
	return fmt.Sprintf("Input Byte at %d", i.Offset)
}

func (i Input) MemOffset() int {
	return i.Offset
}

type Output struct {
	Offset int
}

func (i Output) Instruction() string {
	return fmt.Sprintf("Output Byte at %d", i.Offset)
}

func (i Output) MemOffset() int {
	return i.Offset
}

// StartLoop instruction signals the start of a loop, after moving the
// pointer by the given offset.
type StartLoop struct {
	Offset int
}

func (s StartLoop) Instruction() string {
	return fmt.Sprintf("Start Loop at %d", s.Offset)
}

func (s StartLoop) MemOffset() int {
	return s.Offset
}

// EndLoop instruction signals the end of a loop.
type EndLoop struct {
	Offset int
}

func (e EndLoop) Instruction() string {
	return fmt.Sprintf("End Loop at %d", e.Offset)
}

func (e EndLoop) MemOffset() int {
	return 0
}

// Set sets value of the cell at the given offset from the current cell to
// the given value.
type Set struct {
	X      byte
	Offset int
}

func (c Set) Instruction() string {
	return fmt.Sprintf("Set %d at %d", c.X, c.Offset)
}

func (c Set) MemOffset() int {
	return c.Offset
}
