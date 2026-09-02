; Clean-room stage 1 title kernel.
; This bank deliberately draws only the first O and its coral interior. It
; does not depend on playfield state from any other title stage.

        processor 6502
        include "vcs.h"
        include "macro.h"

STATE_TITLE      = 3
GAME_STATE       = $80
BANK1_SELECT     = $FFF9
COLOR_BLACK      = $00
COLOR_TITLE_PINK = $4A
COLOR_TITLE_WHITE = $0E

        seg Code
        org $0000
        rorg $F000

Bank0Reset:
        CLEAN_START
        ; F8 normally starts in bank 1. Route a bank-0 reset through the
        ; verified game reset so the main frame owns VSYNC and the stage
        ; renderer is entered at the normal title handoff point.
        sta BANK1_SELECT
        jmp $F000

        org $00B6
        rorg $F0B6
Bank0TitleEntry:
        jmp Stage1Title

        org $0100
        rorg $F100

; Each routine consumes one complete visible scanline. The O body is one
; solid PF1 span. COLUPF changes white -> coral -> white while the beam
; crosses that span, so no player or missile object is needed.
        MAC STAGE1_O_LINE
        lda CineTitlePF0L,x
        sta PF0
        lda #$1F
        sta PF1
        nop
        nop
        lda #COLOR_TITLE_WHITE
        sta COLUPF
        IFCONST TITLE_STAGE2
        lda #$04             ; C vertical stroke beside the verified O body.
        ELSE
        lda #$00
        ENDIF
        sta PF2
        lda #COLOR_TITLE_PINK
        sta COLUPF
        sty COLUPF
        nop
        IFCONST TITLE_STAGE2
        lda #$80
        sta PF0
        lda #$08
        sta PF1
        lda #$81
        sta PF2
        ELSE
        lda #$00
        sta PF0
        lda #$00
        sta PF1
        lda #$80
        sta PF2
        ENDIF
        nop
        nop
        nop
        nop
        nop
        nop
        lda #COLOR_TITLE_PINK
        sta COLUPF
        sta WSYNC
        jmp {1}
        ENDM

        MAC STAGE1_O_LINE_NEXT
        lda CineTitlePF0L,x
        sta PF0
        lda #$1F
        sta PF1
        nop
        nop
        lda #COLOR_TITLE_WHITE
        sta COLUPF
        IFCONST TITLE_STAGE2
        lda #$04             ; C vertical stroke beside the verified O body.
        ELSE
        lda #$00
        ENDIF
        sta PF2
        lda #COLOR_TITLE_PINK
        sta COLUPF
        sty COLUPF
        nop
        IFCONST TITLE_STAGE2
        lda #$80
        sta PF0
        lda #$08
        sta PF1
        lda #$81
        sta PF2
        ELSE
        lda #$00
        sta PF0
        lda #$00
        sta PF1
        lda #$80
        sta PF2
        ENDIF
        nop
        nop
        nop
        nop
        nop
        nop
        lda #COLOR_TITLE_PINK
        sta COLUPF
        inx
        sta WSYNC
        jmp {1}
        ENDM

        MAC STAGE1_NORMAL_FIRST
        lda CineTitlePF0L,x
        sta PF0
        lda CineTitlePF1L,x
        sta PF1
        lda CineTitlePFColors,x
        nop
        sta COLUPF
        lda CineTitlePF2L,x
        sta PF2
        lda CineTitlePF0R,x
        sta PF0
        lda CineTitlePF1R,x
        sta PF1
        lda CineTitlePF2R,x
        sta PF2
        nop
        nop
        nop
        nop
        nop
        nop
        nop
        lda #COLOR_TITLE_PINK
        sta COLUPF
        sta WSYNC
        jmp {1}
        ENDM

        MAC STAGE1_NORMAL_SECOND
        lda CineTitlePF0L,x
        sta PF0
        lda CineTitlePF1L,x
        sta PF1
        lda CineTitlePFColors,x
        nop
        sta COLUPF
        lda CineTitlePF2L,x
        sta PF2
        lda CineTitlePF0R,x
        sta PF0
        lda CineTitlePF1R,x
        sta PF1
        lda CineTitlePF2R,x
        sta PF2
        inx
        IFCONST TITLE_STAGE2
        ; Stage 2 places the second O near the right edge. Keep its second
        ; physical scanline white until the beam has passed the full glyph.
        ; Six NOPs replace the timing otherwise supplied by the row-loop
        ; comparison below and still restore coral before the right border.
        nop
        nop
        nop
        nop
        nop
        nop
        ENDIF
        lda #COLOR_TITLE_PINK
        sta COLUPF
        sta WSYNC
        jmp {1}
        ENDM

; Stage 3 draws the A's two coral rows with the playfield alone. The G and
; the A's left rail remain white, COLUPF turns coral across the A interior,
; then returns to white for its right rail. Both physical scanlines use the
; same fixed-cycle schedule.
        MAC STAGE3_A_LINE
        lda CineTitlePF0L,x
        sta PF0
        lda CineTitlePF1L,x
        sta PF1
        nop
        lda #COLOR_TITLE_WHITE
        sta COLUPF
        lda CineTitlePF2L,x
        sta PF2
        IFCONST TITLE_STAGE4
        lda #$60             ; M left pair on A's coral rows.
        ELSE
        lda #$00
        ENDIF
        sta PF0
        nop
        lda #COLOR_TITLE_PINK
        sta COLUPF
        sty COLUPF
        IFCONST TITLE_STAGE5
        lda #$CF             ; M right pair, white E rail, coral stripe.
        ELSE
        IFCONST TITLE_STAGE4
        lda #$C0             ; M right pair on A's coral rows.
        ELSE
        lda #$00
        ENDIF
        ENDIF
        sta PF1
        lda #$80
        sta PF2
        lda #COLOR_TITLE_PINK
        sta COLUPF
        sta WSYNC
        jmp {1}
        ENDM

        MAC STAGE3_A_LINE_NEXT
        lda CineTitlePF0L,x
        sta PF0
        lda CineTitlePF1L,x
        sta PF1
        nop
        lda #COLOR_TITLE_WHITE
        sta COLUPF
        lda CineTitlePF2L,x
        sta PF2
        IFCONST TITLE_STAGE4
        lda #$60             ; M left pair on A's coral rows.
        ELSE
        lda #$00
        ENDIF
        sta PF0
        nop
        lda #COLOR_TITLE_PINK
        sta COLUPF
        sty COLUPF
        IFCONST TITLE_STAGE5
        lda #$CF             ; M right pair, white E rail, coral stripe.
        ELSE
        IFCONST TITLE_STAGE4
        lda #$C0             ; M right pair on A's coral rows.
        ELSE
        lda #$00
        ENDIF
        ENDIF
        sta PF1
        lda #$80
        sta PF2
        lda #COLOR_TITLE_PINK
        sta COLUPF
        inx
        sta WSYNC
        jmp {1}
        ENDM

; Stage 5 lower E stripe rows use the same fixed-cycle color schedule as the
; accepted A rows. The early color writes both hold white, keeping G, A, M,
; and the E rail unchanged. The final coral write begins at E column 29,
; coloring only columns 29 through 31 before continuing to the frame edge.
        MAC STAGE5_E_LINE
        lda CineTitlePF0L,x
        sta PF0
        lda CineTitlePF1L,x
        sta PF1
        nop
        lda #COLOR_TITLE_WHITE
        sta COLUPF
        lda CineTitlePF2L,x
        sta PF2
        lda #$20             ; M left rail on E's lower stripe rows.
        sta PF0
        nop
        lda #COLOR_TITLE_WHITE
        sta COLUPF
        sty COLUPF
        lda #$4F             ; M right rail, white E rail, coral stripe.
        sta PF1
        lda #$80             ; Right coral frame edge.
        sta PF2
        lda #COLOR_TITLE_PINK
        sta COLUPF
        sta WSYNC
        jmp {1}
        ENDM

        MAC STAGE5_E_LINE_NEXT
        lda CineTitlePF0L,x
        sta PF0
        lda CineTitlePF1L,x
        sta PF1
        nop
        lda #COLOR_TITLE_WHITE
        sta COLUPF
        lda CineTitlePF2L,x
        sta PF2
        lda #$20             ; M left rail on E's lower stripe rows.
        sta PF0
        nop
        lda #COLOR_TITLE_WHITE
        sta COLUPF
        sty COLUPF
        lda #$4F             ; M right rail, white E rail, coral stripe.
        sta PF1
        lda #$80             ; Right coral frame edge.
        sta PF2
        lda #COLOR_TITLE_PINK
        sta COLUPF
        inx
        sta WSYNC
        jmp {1}
        ENDM

Stage1Title:
Stage1Visible:
        ; Bank 1 has already issued VSYNC and waited for its VBLANK timer.
        ; Draw only the staged visible section here, then return to bank 1 for
        ; a fixed blank remainder. Starting another VSYNC sequence here would
        ; make the title drift vertically inside the parent frame.
        lda #$00
        sta CTRLPF
        sta NUSIZ0
        sta NUSIZ1
        lda #$00
        IFCONST TITLE_STAGE6_MUSIC
        ; Bank 1 has already advanced and written the original title music.
        ; Six harmless three-cycle RAM reads exactly replace the six
        ; three-cycle audio stores. Code size and raster timing are unchanged.
        bit GAME_STATE
        bit GAME_STATE
        bit GAME_STATE
        bit GAME_STATE
        bit GAME_STATE
        bit GAME_STATE
        ELSE
        sta AUDC0
        sta AUDC1
        sta AUDF0
        sta AUDF1
        sta AUDV0
        sta AUDV1
        ENDIF
        sta GRP0
        sta GRP1
        sta ENAM0
        sta ENAM1
        sta ENABL
        sta VDELP0
        sta VDELP1
        lda #COLOR_BLACK
        sta COLUBK
        lda #COLOR_TITLE_WHITE
        sta COLUP0
        sta COLUP1
        lda #$00
        sta GRP0
        sta GRP1
        lda #COLOR_TITLE_PINK
        sta COLUPF
        ldx #0
        ldy #COLOR_TITLE_WHITE
        lda CineTitlePF0L,x
        sta PF0
        lda CineTitlePF1L,x
        sta PF1
        lda CineTitlePF2L,x
        sta PF2
        lda #$00
        sta WSYNC
        sta VBLANK
        jmp Stage1Row0First

        ; Keep the fixed return trampoline at the address expected by the
        ; parent title frame. The expanded scanline routines begin on the
        ; following page, as in the verified F8 title bank.
        ; Two instructions occupy five bytes, so begin at F3BB. The bank
        ; switch must finish exactly at F3C0, the first byte of bank 1's
        ; stage continuation.
        org $03BB
        rorg $F3BB
Stage1BankReturn:
        lda #$00
        sta BANK1_SELECT

        org $0400
        rorg $F400

Stage1Row0First:
        STAGE1_NORMAL_FIRST Stage1Row0Second
Stage1Row0Second:
        STAGE1_NORMAL_SECOND Stage1Row1First
Stage1Row1First:
        STAGE1_NORMAL_FIRST Stage1Row1Second
Stage1Row1Second:
        STAGE1_NORMAL_SECOND Stage1Row2First
Stage1Row2First:
        STAGE1_NORMAL_FIRST Stage1Row2Second
Stage1Row2Second:
        STAGE1_NORMAL_SECOND Stage1Row3First
Stage1Row3First:
        STAGE1_NORMAL_FIRST Stage1Row3Second
Stage1Row3Second:
        STAGE1_NORMAL_SECOND Stage1Row4First
Stage1Row4First:
        STAGE1_NORMAL_FIRST Stage1Row4Second
Stage1Row4Second:
        STAGE1_NORMAL_SECOND Stage1Row5First

; Only the first O is enabled in stage 1. Its cap rows use the ordinary
; table-driven schedule. Its five solid body rows use the fixed-cycle COLUPF
; schedule, changing only the middle color as the beam traces the O.
Stage1Row5First:
        STAGE1_NORMAL_FIRST Stage1Row5Second
Stage1Row5Second:
        STAGE1_NORMAL_SECOND Stage1Row6First
Stage1Row6First:
        STAGE1_O_LINE Stage1Row6Second
Stage1Row6Second:
        STAGE1_O_LINE_NEXT Stage1Row7First
Stage1Row7First:
        STAGE1_O_LINE Stage1Row7Second
Stage1Row7Second:
        STAGE1_O_LINE_NEXT Stage1Row8First
Stage1Row8First:
        STAGE1_O_LINE Stage1Row8Second
Stage1Row8Second:
        STAGE1_O_LINE_NEXT Stage1Row9First
Stage1Row9First:
        STAGE1_O_LINE Stage1Row9Second
Stage1Row9Second:
        STAGE1_O_LINE_NEXT Stage1Row10First
Stage1Row10First:
        STAGE1_O_LINE Stage1Row10Second
Stage1Row10Second:
        STAGE1_O_LINE_NEXT Stage1Row11First
Stage1Row11First:
        IFCONST TITLE_STAGE2
Stage2RowsFirst:
        STAGE1_NORMAL_FIRST Stage2RowsSecond
        ELSE
        STAGE1_NORMAL_FIRST Stage1Row11Second
        ENDIF
Stage1Row11Second:
        STAGE1_NORMAL_SECOND Stage1Row12First
Stage1Row12First:
        STAGE1_NORMAL_FIRST Stage1Row12Second
Stage1Row12Second:
        STAGE1_NORMAL_SECOND Stage1TitleDone

        IFCONST TITLE_STAGE2
; Rows 11 through 22 contain the lower O cap, two blank separator rows, and G.
; They use the ordinary fixed playfield schedule, so stage 2 adds no new
; mid-scanline color transitions beyond the already verified first O.
Stage2RowsSecond:
        lda CineTitlePF0L,x
        sta PF0
        lda CineTitlePF1L,x
        sta PF1
        lda CineTitlePFColors,x
        nop
        sta COLUPF
        lda CineTitlePF2L,x
        sta PF2
        lda CineTitlePF0R,x
        sta PF0
        lda CineTitlePF1R,x
        sta PF1
        lda CineTitlePF2R,x
        sta PF2
        inx
        ; The loop comparison contributes four cycles on ordinary rows.
        ; Add eight more so the lower cap of the second O finishes in white
        ; before COLUPF returns to coral for the right frame edge.
        IFCONST TITLE_STAGE6
        ; Stage 6 continues beyond the accepted lettering at row 23.
        cpx #23
        beq Stage6RowsStart
        cpx #16
        bne Stage4RowsNotA
        jmp Stage3RowsAStart
Stage4RowsNotA:
        bit GAME_STATE
        ELSE
        IFCONST TITLE_STAGE4
        ; Stage 4 needs an early last-row exit because M leaves visible data
        ; in the right-half registers. Ordinary rows retain the same twelve
        ; dispatch cycles as stage 3.
        cpx #23
        beq Stage4RowsLast
        cpx #16
        bne Stage4RowsNotA
        jmp Stage3RowsAStart
Stage4RowsNotA:
        bit GAME_STATE
        ELSE
        IFCONST TITLE_STAGE3
        ; This three-cycle pad plus the five-cycle not-A test exactly
        ; replaces stage 2's four NOPs on ordinary rows.
        bit GAME_STATE
        cpx #16
        bne Stage3RowsNotA
        jmp Stage3RowsAStart
Stage3RowsNotA:
        ELSE
        nop
        nop
        nop
        nop
        ENDIF
        ENDIF
        ENDIF
        IFCONST TITLE_STAGE6
        ELSE
        IFCONST TITLE_STAGE4
        ELSE
        IFCONST TITLE_STAGE3
        cpx #23
        beq Stage3RowsLast
        ELSE
        cpx #23
        beq Stage2RowsLast
        ENDIF
        ENDIF
        ENDIF
        lda #COLOR_TITLE_PINK
        sta COLUPF
        sta WSYNC
        jmp Stage2RowsFirst
        IFCONST TITLE_STAGE6
Stage6RowsStart:
        ; Reuse stage 5's accepted cleanup at the text/lower-scene seam.
        ; This completes E's white bottom cap, then uses the following blank
        ; scanline as the first physical copy of lower-scene row 23.
        nop
        lda #COLOR_TITLE_PINK
        sta COLUPF
        lda #$00
        sta WSYNC
        sta PF0
        sta PF1
        sta PF2
        ; Prepare the title-only octopus while the blank row is traced. These
        ; Setup plus the pad below replaces stage 5's 36-cycle NOP block.
        lda #$07
        sta NUSIZ0
        lda #$BA
        sta COLUP0
        ; The accepted A transition consumes one extra scanline. Row 23 is
        ; empty, so draw it once instead of twice to retain the original
        ; 132-line scene budget without changing any approved text pixels.
        inx
        lda CineTitlePlayer,x
        sta GRP0
        bit GAME_STATE
        nop
        nop
        nop
        nop
        nop
        nop
        nop
        lda #$80
        sta PF2
        sta WSYNC
        jmp Stage6RowsFirst

Stage6RowsFirst:
        lda CineTitlePF0L,x
        sta PF0
        lda CineTitlePF1L,x
        sta PF1
        lda CineTitlePFColors,x
        tay
        lda CineTitlePF2L,x
        sty COLUPF
        sta PF2
        lda CineTitlePF0R,x
        sta PF0
        lda CineTitlePF1R,x
        sta PF1
        lda CineTitlePF2R,x
        sta PF2
        nop
        nop
        nop
        nop
        nop
        nop
        nop
        lda #COLOR_TITLE_PINK
        sta COLUPF
        sta WSYNC

Stage6RowsSecond:
        lda CineTitlePF0L,x
        sta PF0
        lda CineTitlePF1L,x
        sta PF1
        lda CineTitlePFColors,x
        tay
        lda CineTitlePF2L,x
        sty COLUPF
        sta PF2
        lda CineTitlePF0R,x
        sta PF0
        lda CineTitlePF1R,x
        sta PF1
        lda CineTitlePF2R,x
        sta PF2
        inx
        cpx #66
        beq Stage6RowsDone
        lda CineTitlePlayer,x
        sta GRP0
        lda #COLOR_TITLE_PINK
        sta COLUPF
        sta WSYNC
        jmp Stage6RowsFirst
Stage6RowsDone:
        jmp Stage1BankReturn
        ENDIF
        IFCONST TITLE_STAGE4
Stage4RowsLast:
        IFCONST TITLE_STAGE5
        ; Let the second physical scanline of E's bottom cap finish in white
        ; before restoring coral for the far-right frame edge.
        nop
        ENDIF
        lda #COLOR_TITLE_PINK
        sta COLUPF
        lda #$00
        sta WSYNC
        sta PF0
        sta PF1
        ; Clear the left-half PF2 value from the bottom of A before it can
        ; repeat as a coral dash between A and M on this final blank line.
        sta PF2
        ; Wait until the beam has passed the left PF2 region, then restore
        ; only the right-edge border bit for the asymmetric right half.
        nop
        nop
        nop
        nop
        nop
        nop
        nop
        nop
        nop
        nop
        nop
        nop
        nop
        nop
        nop
        nop
        nop
        nop
        lda #$80
        sta PF2
        sta WSYNC
        jmp Stage1TitleDone
        ENDIF
        IFCONST TITLE_STAGE3
Stage3RowsLast:
        lda #COLOR_TITLE_PINK
        sta COLUPF
        sta WSYNC
        jmp Stage1TitleDone

Stage3RowsAStart:
        lda #COLOR_TITLE_PINK
        sta COLUPF
        sta WSYNC
        jmp Stage3Row16First

Stage3Row16First:
        STAGE3_A_LINE Stage3Row16Second
Stage3Row16Second:
        STAGE3_A_LINE_NEXT Stage3Row17First
Stage3Row17First:
        STAGE3_A_LINE Stage3Row17Second
Stage3Row17Second:
        IFCONST TITLE_STAGE5
        STAGE3_A_LINE_NEXT Stage5Row18First
        ELSE
        STAGE3_A_LINE_NEXT Stage2RowsFirst
        ENDIF
        IFCONST TITLE_STAGE5
Stage5Row18First:
        STAGE1_NORMAL_FIRST Stage5Row18Second
Stage5Row18Second:
        STAGE1_NORMAL_SECOND Stage5Row19First
Stage5Row19First:
        STAGE1_NORMAL_FIRST Stage5Row19Second
Stage5Row19Second:
        STAGE1_NORMAL_SECOND Stage5Row20First

Stage5Row20First:
        STAGE5_E_LINE Stage5Row20Second
Stage5Row20Second:
        STAGE5_E_LINE_NEXT Stage5Row21First
Stage5Row21First:
        STAGE5_E_LINE Stage5Row21Second
Stage5Row21Second:
        STAGE5_E_LINE_NEXT Stage2RowsFirst
        ENDIF
        ENDIF
Stage2RowsLast:
        lda #COLOR_TITLE_PINK
        sta COLUPF
        sta WSYNC
        jmp Stage1TitleDone
        ENDIF

Stage1TitleDone:
        lda #COLOR_BLACK
        sta COLUPF
        sta PF0
        sta PF1
        sta PF2
        ; Return to the parent frame. Bank 1's stage continuation consumes
        ; the remaining visible lines and then runs the ordinary overscan.
        jmp Stage1BankReturn

        IFCONST TITLE_STAGE6
        org $0D00
        rorg $FD00
        include "src/title_stage6_direct_data.inc"
        ELSE
        IFCONST TITLE_STAGE5
        org $0D00
        rorg $FD00
        include "src/title_stage5_direct_data.inc"
        ELSE
        org $0C00
        rorg $FC00
        IFCONST TITLE_STAGE4
        include "src/title_stage4_direct_data.inc"
        ELSE
        IFCONST TITLE_STAGE3
        include "src/title_stage3_direct_data.inc"
        ELSE
        IFCONST TITLE_STAGE2
        include "src/title_stage2_direct_data.inc"
        ELSE
        include "src/title_stage1_direct_data.inc"
        ENDIF
        ENDIF
        ENDIF
        ENDIF
        ENDIF

        org $0FFA
        rorg $FFFA
        word Bank0Reset
        word Bank0Reset
        word Bank0Reset

        end
