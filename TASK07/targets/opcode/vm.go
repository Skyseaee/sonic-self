package opcode

import (
	"fmt"
	"io"
	"os"
)

type vm struct {
	memory  []byte
	pointer int
}

type printBuffer struct {
	buffer []byte

	writer    io.Writer
	autoFlush bool
	length    int
}

func (b *printBuffer) Write(bytes ...byte) {
	b.buffer = append(b.buffer, bytes...)

	if b.autoFlush && len(b.buffer) > b.length {
		b.Flush()
	}
}

func (b *printBuffer) Flush() {
	if len(b.buffer) == 0 {
		return
	}

	b.writer.Write(b.buffer)
	b.buffer = []byte{}
}

func Run(oc []int) {
	v := vm{memory: make([]byte, 30000)}
	buffer := printBuffer{
		writer:    os.Stdout,
		autoFlush: true,
		length:    50,
	}
	length := len(oc)
	for i := 0; i < length; i++ {
		switch Opcode(oc[i]) {
		case ChangeValue:
			pointer := v.pointer + oc[i+1]
			v.memory[pointer] += byte(oc[i+2])
			i += 2
		case InputByte:
			i++
			pointer := v.pointer + oc[i]
			fmt.Scanf("%c", &v.memory[pointer])
		case OutputByte:
			i++
			pointer := v.pointer + oc[i]
			buffer.Write(v.memory[pointer])
		case JumpIfZero:
			i++
			v.pointer += oc[i]

			i++
			jump := oc[i]

			if v.memory[v.pointer] == 0 {
				i += jump
			}
		case JumpIfNotZero:
			i++
			v.pointer += oc[i]

			i++
			jump := oc[i]

			if v.memory[v.pointer] != 0 {
				i -= jump
			}
		case SetValue:
			i++
			pointer := v.pointer + oc[i]

			i++
			value := byte(oc[i])

			v.memory[pointer] = value
		default:
			panic(fmt.Sprintf("opcode: run: invalid opcode %x", uint(oc[i])))
		}
	}

	buffer.Flush()
}
