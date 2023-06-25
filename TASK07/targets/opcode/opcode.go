// Package opcode implements the opcode compilation target. It provides
// structures and methods to compile an instruction.Chunk into opcode and
// to run the same.
package opcode

// Opcode represents a single opcode instruction.
type Opcode int

// Various opcode instructions.
const (
	_ Opcode = iota

	InputByte     // [code] [offset]
	OutputByte    // [code] [offset]
	ChangeValue   // [code] [offset] [amount]
	SetValue      // [code] [offset] [amount]
	JumpIfZero    // [code] [offset] [jump-offset]
	JumpIfNotZero // [code] [offset] [jump-offset]
)
