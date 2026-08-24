; Octo Game
; Red Light, Green Light for the Atari 2600, NTSC, 4 KiB.

        processor 6502
        include "vcs.h"
        include "macro.h"

; -----------------------------------------------------------------------------
; Constants
; -----------------------------------------------------------------------------

STATE_PLAY      = 0
STATE_DEAD      = 1
STATE_CLEAR     = 2
STATE_TITLE     = 3
STATE_VICTORY   = 4

LIGHT_GREEN     = 0       ; Doll is facing away, movement is safe.
LIGHT_RED       = 1       ; Doll is watching, movement is fatal.

MODE_ONE_PLAYER = 1       ; Reserved for the later mode-select screen.

PLAYER_START_Y  = 132
PLAYER_START_X  = 76
PLAYER_MIN_X    = 20
PLAYER_MAX_X    = 132
PLAYER_HEIGHT   = 12
PLAYER_WIDTH    = 8
GAME_LINES      = 148

TREE_HEIGHT     = 12
BOULDER_HEIGHT  = 8

HUD_ROWS        = 5
HUD_ROW_LINES   = 4
DOLL_ROWS       = 8

COLOR_BLACK     = $00
COLOR_WHITE     = $0E
COLOR_BLUE      = $84
COLOR_OCTO_GREEN = $C8
COLOR_TREE_GREEN = $D6
COLOR_BOULDER   = $06
COLOR_DARK_BLUE = $82
COLOR_GREEN     = $C8
COLOR_DARK_GREEN = $C2
COLOR_RED       = $46
COLOR_DARK_RED  = $42
COLOR_GOLD      = $1E
COLOR_DOLL_BACK = COLOR_WHITE
COLOR_DOLL_FACE = $3E
COLOR_TITLE_PINK = $4A
COLOR_TITLE_TEAL = $BA

SOUND_NONE      = 0
SOUND_GUNSHOT   = 1
SOUND_CLEAR     = 2
SOUND_RED_CUE   = 3
SOUND_GREEN_CUE = 4

; -----------------------------------------------------------------------------
; RAM, $80-$FF
; -----------------------------------------------------------------------------

        seg.u Variables
        org $80

GameState       ds 1
GameMode        ds 1
Level           ds 1
ScoreHiBCD      ds 1       ; Thousands and hundreds, packed BCD.
ScoreLoBCD      ds 1       ; Tens and ones, packed BCD.
TimerHiBCD      ds 1       ; Hundreds digit, starts at 9.
TimerLoBCD      ds 1       ; Tens and ones, starts at 99.
TimerSubframe   ds 1       ; Five timer ticks per nine NTSC frames.
TimerSkipTick   ds 1       ; Skips one tick so zero lands on frame 1800.
PlayerY         ds 1       ; Position within the 148-line game lane.
PlayerX         ds 1       ; Horizontal coordinate inside the arena.
ObstaclesActive ds 1       ; Set only for levels 2, 4, 6, and 8.
ObstacleX       ds 3       ; Tree, boulder one, boulder two.
ObstacleY       ds 3
LaneColor       ds 1       ; Cached so gray ball rows can restore the border.
LightState      ds 1
PhaseTimer      ds 1
RandomSeed      ds 1
FrameCounter    ds 1
StateTimer      ds 1
SoundTimer      ds 1
SoundKind       ds 1
TitleMusicFrame ds 1
TitleMusicStep  ds 1

Digit0Index     ds 1
Digit1Index     ds 1
Digit2Index     ds 1
Digit3Index     ds 1
Temp            ds 1

; The first five bytes of each display strip hold the normal HUD. The remaining
; ten are reused by the three-line ending without a separate screen buffer.
DisplayText0    ds HUD_ROWS * 3
DisplayText1    ds HUD_ROWS * 3
DisplayText2    ds HUD_ROWS * 3
DisplayText3    ds HUD_ROWS * 3
DisplayText4    ds HUD_ROWS * 3
DisplayText5    ds HUD_ROWS * 3

ScorePF0        = DisplayText0
ScorePF1        = DisplayText1
ScorePF2        = DisplayText2
TimerPF0        = DisplayText3
TimerPF1        = DisplayText4
TimerPF2        = DisplayText5

; -----------------------------------------------------------------------------
; Cartridge ROM, $F000-$FFFF
; -----------------------------------------------------------------------------

        seg Code
        org $F000

Reset:
        CLEAN_START

        lda #$A5
        sta RandomSeed
        lda #MODE_ONE_PLAYER
        sta GameMode
        lda #STATE_TITLE
        sta GameState

        ; Keep the octopus compact while making the distant doll easy to read.
        lda #$07             ; Quad-width P0 for the title-screen mascot.
        sta NUSIZ0
        lda #$05
        sta NUSIZ1
        lda #$01
        sta CTRLPF             ; Reflect the playfield on the right half.

        ; Optional emulator-only entry point for visual regression captures.
        ; Normal cartridge builds never define VICTORY_TEST.
        IFCONST VICTORY_TEST
        lda #$12
        sta ScoreHiBCD
        lda #$34
        sta ScoreLoBCD
        jsr BuildVictoryText
        lda #STATE_VICTORY
        sta GameState
        ENDIF

Frame:
        ; Three scanlines of vertical sync.
        lda #$02
        sta VBLANK
        sta VSYNC
        sta WSYNC
        sta WSYNC
        sta WSYNC
        lda #$00
        sta VSYNC

        ; Game logic and object positioning run during vertical blank.
        lda #43
        sta TIM64T

        IFNCONST VICTORY_TEST
        jsr CheckConsoleReset
        ENDIF
        jsr UpdateGame
        jsr UpdateSound
        jsr SetObjectColors

        ; P0 is the octopus, P1 is the doll. The title mascot sits four color
        ; clocks to the right of the fine-text kernel's P0 position so its
        ; quad-width silhouette is visually centered inside the frame.
        lda GameState
        cmp #STATE_TITLE
        bcc PositionGameOcto
        beq PositionTitleOcto
        lda #56                ; Victory screen's 48-pixel text position.
        bne PositionOcto
PositionTitleOcto:
        lda #60
        bne PositionOcto
PositionGameOcto:
        lda PlayerX
PositionOcto:
        ldx #0
        jsr PositionObject

        lda GameState
        cmp #STATE_TITLE
        bcc PositionGameDoll
        lda #64              ; P1 position for the 48-pixel title text.
        bne PositionDoll
PositionGameDoll:
        lda #72
PositionDoll:
        ldx #1
        jsr PositionObject

        ; M1 and BL draw the two boulders. P1 is moved from the doll to the
        ; tree during the blank gap above the arena.
        lda ObstacleX+1
        ldx #3
        jsr PositionObject
        lda ObstacleX+2
        ldx #4
        jsr PositionObject
        sta WSYNC
        sta HMOVE

        ; Prepare the independent left and right HUD halves while the beam is
        ; still blanked. X and Y survive the timer wait below.
        lda #$00
        sta CTRLPF
        sta GRP0
        sta GRP1
        sta PF0                 ; Do not expose the previous frame while the
        sta PF1                 ; beam is unblanked ahead of the HUD writes.
        sta PF2
        lda #COLOR_WHITE
        sta COLUPF
        ldy #0
        ldx #HUD_ROW_LINES

WaitVBlank:
        lda INTIM
        ; After reaching zero, the RIOT timer underflows and counts at one CPU
        ; cycle per tick. Waiting for exactly zero can miss that brief value
        ; and extend some title frames, which causes a slow vertical crawl.
        bpl WaitVBlank

        lda GameState
        cmp #STATE_TITLE
        bcc DrawGameVisible     ; Preserve the original gameplay path timing.
        beq DrawTitleVisible
        ; STATE_VICTORY is the only remaining visible state.
        sta WSYNC
        jmp VictoryVisible
DrawTitleVisible:
        sta WSYNC             ; Preserve the title's preloading scanline.
        jmp TitleVisible
DrawGameVisible:
        lda #$00
        sta WSYNC             ; Choose the path before syncing, then unblank
        sta VBLANK            ; at the start of a clean gameplay scanline.

; -----------------------------------------------------------------------------
; Visible display, exactly 192 scanlines
; -----------------------------------------------------------------------------

        ; Classic asymmetric playfield trick: draw the four-digit score on the
        ; left, then rewrite PF0-PF2 and COLUPF before the beam reaches the
        ; right half to draw the gold three-digit timer. Neither value mirrors.
HudScanline:
        lda #COLOR_WHITE
        sta COLUPF
        lda ScorePF0,y
        sta PF0
        lda ScorePF1,y
        sta PF1
        lda ScorePF2,y
        sta PF2

        nop
        nop
        lda TimerPF0,y
        sta PF0
        lda TimerPF1,y
        sta PF1
        lda #COLOR_GOLD
        sta COLUPF
        lda TimerPF2,y
        sta PF2

        dex
        bne HudNextLine
        iny
        cpy #HUD_ROWS
        beq HudDone
        ldx #HUD_ROW_LINES
HudNextLine:
        sta WSYNC
        jmp HudScanline

HudDone:
        sta WSYNC             ; Let the final timer pixels finish drawing.
        ; Clear both HUD halves during horizontal blank. If CTRLPF is changed
        ; first, the final gold timer row is briefly reflected onto the left
        ; side of the following scanline.
        stx PF0                ; X is zero after the final HUD row.
        stx PF1
        stx PF2
        lda #$01
        sta CTRLPF             ; Reflect the playfield for the game arena.
        sta ENAM0
        sta ENAM1
        sta ENABL
        lda #$05
        sta NUSIZ1             ; Restore the double-width doll every frame.

        ; Doll lane: two blank lines, sixteen doubled sprite lines, two blanks.
        lda #0
        sta PF0
        sta PF1
        sta PF2
        sta WSYNC
        sta WSYNC

        ldx #0
DollKernel:
        lda LightState
        beq DrawDollBack
        lda DollFaceSprite,x
        bne DrawDollRow
DrawDollBack:
        lda DollBackSprite,x
DrawDollRow:
        sta GRP1
        sta WSYNC
        sta WSYNC
        inx
        cpx #DOLL_ROWS
        bne DollKernel

        lda #0
        sta GRP1

        ; Reuse P1 for the tree. The two positioning lines are inside the
        ; existing blank gap, and VBLANK hides the visible HMOVE comb. Keep
        ; the second line fully blank while preloading the finish stripe so
        ; no partially unblanked yellow line can appear.
        lda #$02
        sta VBLANK
        lda ObstaclesActive
        beq NoBoulderPosition
        sta HMCLR             ; The following HMOVE must adjust P1 only.
        lda ObstacleX
        ldx #1
        jsr PositionObject
        jmp BoulderPositioned
NoBoulderPosition:
        sta WSYNC
BoulderPositioned:
        sta WSYNC
        sta HMOVE

        ; Preload a clean three-line finish stripe while VBLANK is still set.
        ; This occupies the same total scanline budget as the old partial plus
        ; three-line stripe, but every visible yellow row is now complete.
        lda #COLOR_GOLD
        sta COLUPF
        lda #$F0
        sta PF0
        lda #$FF
        sta PF1
        sta PF2
        sta WSYNC
        lda #$00
        sta VBLANK
        sta WSYNC
        sta WSYNC

        ; Choose the arena color while the beam is still drawing the final
        ; yellow stripe line. A survives WSYNC, letting every arena register
        ; update land inside the following horizontal blank.
        jsr LoadLaneColor
        sta WSYNC

        ; Main game lane, 148 scanlines. SkipDraw positions the octopus.
        sta COLUPF
        sta LaneColor
        lda #$10
        sta PF0
        lda #$00
        sta PF1
        sta PF2
        lda #COLOR_TREE_GREEN
        sta COLUP1
        lda #$30               ; Normal P1 and an eight-pixel-wide M1 rock.
        sta NUSIZ1
        lda #$31               ; Reflected playfield and eight-pixel ball.
        sta CTRLPF
        lda #$00
        sta GRP1
        sta ENAM1
        sta ENABL

        ldy #0
TreeGameKernel:
        tya
        sec
        sbc PlayerY
        bpl TreePlayerIndex
        lda #$00
        beq StoreTreePlayer
TreePlayerIndex:
        tax
        lda OctoLineTable,x
StoreTreePlayer:
        sta GRP0

        ; Prepare the following tree scanline after the current pixels pass.
        tya
        clc
        adc #1
        sec
        sbc ObstacleY
        bcc ClearNextTree
        cmp #TREE_HEIGHT
        bcs ClearNextTree
        tax
        lda TreeSprite,x
        nop
        nop
        sta GRP1
        lda #$00
        sta ENAM1
        sta ENABL
        jmp TreeRowReady
ClearNextTree:
        nop
        nop
        nop
        nop
        lda #$00
        sta GRP1
        sta ENAM1
        sta ENABL
TreeRowReady:
        sta WSYNC
        iny
        cpy #59
        bne TreeGameKernel

        ; The tree is above both rocks, so P1/M1 can remain gray from here to
        ; the bottom of the frame without a per-row color change.
        lda #COLOR_BOULDER
        sta COLUP1

Boulder1GameKernel:
        tya
        sec
        sbc PlayerY
        bpl Boulder1PlayerIndex
        lda #$00
        beq StoreBoulder1Player
Boulder1PlayerIndex:
        tax
        lda OctoLineTable,x
StoreBoulder1Player:
        sta GRP0

        tya
        clc
        adc #1
        sec
        sbc ObstacleY+1
        bcc ClearNextBoulder1
        cmp #BOULDER_HEIGHT
        bcs ClearNextBoulder1
        nop
        nop
        lda #$02
        sta ENAM1
        lda #$00
        sta GRP1
        sta ENABL
        jmp Boulder1RowReady
ClearNextBoulder1:
        nop
        nop
        nop
        nop
        lda #$00
        sta GRP1
        sta ENAM1
        sta ENABL
Boulder1RowReady:
        sta WSYNC
        iny
        cpy #91
        bne Boulder1GameKernel

Boulder2GameKernel:
        tya
        sec
        sbc PlayerY
        bpl Boulder2PlayerIndex
        lda #$00
        beq StoreBoulder2Player
Boulder2PlayerIndex:
        tax
        lda OctoLineTable,x
StoreBoulder2Player:
        sta GRP0

        ; BL shares COLUPF with the arena. Change COLUPF only after the left
        ; border has passed, then restore it before the right border arrives.
        ; The ball is constrained to the inner 60 percent, so it remains gray
        ; while both playfield borders retain the current lane color.
        SLEEP 4
        lda #COLOR_BOULDER
        sta COLUPF

        tya
        clc
        adc #1
        sec
        sbc ObstacleY+2
        bcc ClearNextBoulder2
        cmp #BOULDER_HEIGHT
        bcs ClearNextBoulder2
        nop
        nop
        lda #$02
        sta ENABL
        jmp Boulder2RowReady
ClearNextBoulder2:
        nop
        nop
        nop
        nop
        lda #$00
        sta ENABL
Boulder2RowReady:
        lda LaneColor
        sta COLUPF
        sta WSYNC
        iny
        cpy #GAME_LINES
        bne Boulder2GameKernel

GameKernelDone:
        lda #0
        sta GRP0
        sta GRP1
        sta ENAM1
        sta ENABL
        sta PF0
        sta PF1
        sta PF2
        ; Complete the gameplay kernel's 192-line budget with one clean bottom
        ; blank. A second line here would produce a 263-line frame.
        sta WSYNC

BeginOverscan:
        lda #$02
        sta VBLANK

        ; Count overscan scanlines directly. A RIOT timer can expire at a
        ; different horizontal position when the preceding title kernel ends,
        ; which lets the picture's vertical phase creep by a scanline even
        ; though Stella still reports a 262-line frame.
        ldx #28
WaitOverscan:
        sta WSYNC
        dex
        bne WaitOverscan
        jmp Frame

; -----------------------------------------------------------------------------
; Ending screen. The commercial-style 48-pixel kernel draws a larger green
; survival line, a readable label, and a four-times-tall five-digit score.
; -----------------------------------------------------------------------------

VictoryVisible:
        lda #$00
        sta CTRLPF
        sta PF0
        sta PF1
        sta PF2
        sta GRP0
        sta GRP1
        sta COLUBK
        lda #$03
        sta NUSIZ0
        sta NUSIZ1
        lda #COLOR_OCTO_GREEN
        sta COLUP0
        sta COLUP1
        lda #$01
        sta VDELP0
        sta VDELP1
        lda #$00
        sta WSYNC
        sta VBLANK

        ldx #56
VictoryTopBlank:
        sta WSYNC
        dex
        bne VictoryTopBlank

        lda #69
        sta StateTimer

VictoryTextKernel:
        ldy StateTimer
        lda VictoryRowMap,y
        tay
        lda DisplayText0,y
        sta WSYNC
        sta GRP0
        lda DisplayText1,y
        sta GRP1
        lda DisplayText2,y
        sta GRP0
        lda DisplayText3,y
        sta Temp
        lda DisplayText4,y
        tax
        lda DisplayText5,y
        ldy Temp
        dec StateTimer
        sty GRP1
        stx GRP0
        sta GRP1
        sta GRP0
        ldy StateTimer
        bpl VictoryTextKernel

VictoryTextDone:
        lda #0
        sta GRP0
        sta GRP1
        sta VDELP0
        sta VDELP1
        ldx #66
VictoryBottomBlank:
        sta WSYNC
        dex
        bne VictoryBottomBlank
        jmp BeginOverscan

; -----------------------------------------------------------------------------
; Intro screen, 66 cinematic rows at two scanlines each, followed by a
; commercial-style 48-pixel fine-text kernel.
; -----------------------------------------------------------------------------

TitleVisible:
        ; The title is staged like a miniature scene: a framed playfield title,
        ; a quad-width hardware-sprite mascot on a stepped pedestal, a prompt,
        ; and a contrasting copyright footer.
        lda #$00
        sta CTRLPF
        sta GRP1
        lda #$07
        sta NUSIZ0

        ; Slowly pulse the octopus between two teal luminance values.
        lda FrameCounter
        and #$20
        beq TitleOctoDim
        lda #$BA
        bne TitleOctoColorReady
TitleOctoDim:
        lda #$B6
        nop                   ; Match the bright path's cycle count exactly.
TitleOctoColorReady:
        sta COLUP0

        ldx #0
        lda CineTitlePlayer,x
        sta GRP0
        lda #COLOR_BLACK
        sta COLUBK
        lda #COLOR_TITLE_PINK
        sta COLUPF
        lda CineTitlePF0L,x
        sta PF0
        lda CineTitlePF1L,x
        sta PF1
        lda CineTitlePF2L,x
        sta PF2
        lda #$00
        sta WSYNC
        sta VBLANK

TitleFirstScanline:
        ; Both doubled scanlines enter here at cycle 3. The playfield begins
        ; pink for the left frame edge, switches to the row's interior color,
        ; then returns to pink just before the right frame edge. This lets the
        ; title be white and the pedestal blue without punching holes through
        ; the pink frame.
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
        jmp TitleSecondScanline

TitleSecondScanline:
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
        cpx #66
        beq TitleTextSetup
        lda CineTitlePlayer,x
        sta GRP0
        lda #COLOR_TITLE_PINK
        sta COLUPF
        sta WSYNC
        jmp TitleFirstScanline

; The playfield is four color clocks per pixel, which is too coarse for small
; credits.  Reuse both players in three-copies-close mode and rewrite GRP0/1
; six times per scanline.  VDEL exposes the hidden graphics latches, producing
; a centered 48-pixel strip like the fine-print kernels in commercial games.
TitleTextSetup:
        ; P0 and P1 were positioned during vertical blank. Finish the last
        ; border scanline before switching to the compact-text footer.
        sta WSYNC
        lda #0
        sta PF0                 ; Clear the old border data first, while the
        sta PF1                 ; beam is still in horizontal blank.
        sta PF2
        lda #COLOR_DARK_RED
        sta COLUBK
        lda #0
        sta GRP0
        sta GRP1
        lda #$03
        sta NUSIZ0
        sta NUSIZ1
        lda #COLOR_GOLD
        sta COLUP0
        sta COLUP1
        lda #1
        sta VDELP0
        sta VDELP1
        lda #56
        sta StateTimer          ; Free for use as a title-only row counter.

        ; Reposition P0 from the visually centered mascot coordinate to the
        ; 48-pixel text coordinate. VBLANK hides both positioning lines and
        ; the HMOVE comb, preserving the title's exact scanline budget.
        lda #$02
        sta VBLANK
        sta HMCLR
        lda #56
        ldx #0
        jsr PositionObject
        sta WSYNC
        sta HMOVE
        sta WSYNC             ; Release VBLANK only at a scanline boundary.
        lda #$00
        sta VBLANK

TitleTextKernel:
        ldy StateTimer
        lda CompactText0,y
        sta WSYNC
        sta GRP0
        lda CompactText1,y
        sta GRP1
        lda CompactText2,y
        sta GRP0
        lda CompactText3,y
        sta Temp
        lda CompactText4,y
        tax
        lda CompactText5,y
        ldy Temp
        nop
        cpx GameState          ; A harmless three-cycle delay.
        sty GRP1
        stx GRP0
        sta GRP1
        sta GRP0               ; Flush the final delayed P1 value.
        dec StateTimer
        bpl TitleTextKernel

        lda #0
        sta GRP0
        sta GRP1
        sta VDELP0
        sta VDELP1
        jmp BeginOverscan

; -----------------------------------------------------------------------------
; Game logic
; -----------------------------------------------------------------------------

CheckConsoleReset:
        lda SWCHB
        and #%00000001
        bne ConsoleResetDone
        jmp Reset
ConsoleResetDone:
        rts

UpdateGame:
        inc FrameCounter

        lda GameState
        beq UpdatePlaying
        cmp #STATE_TITLE
        beq UpdateTitle
        cmp #STATE_DEAD
        beq UpdateDead
        cmp #STATE_CLEAR
        beq UpdateClear
        jmp UpdateDone

        ; Brief celebration, then begin a faster level.
UpdateClear:
        dec StateTimer
        beq AdvanceLevel
        rts
AdvanceLevel:
        lda Level
        cmp #9
        beq EndGame
        inc Level
        jsr StartLevel
        rts
EndGame:
        jsr BuildVictoryText
        lda #STATE_VICTORY
        sta GameState
        rts

UpdateDead:
        ; Fire restarts from level one. Select is reserved for mode selection.
        bit INPT4
        bmi UpdateDone
        jmp NewGame

UpdateTitle:
        ; The controller Fire input is active low. Console Reset returns here,
        ; while Fire begins a clean one-player game.
        bit INPT4
        bmi UpdateDone

NewGame:
        lda #1
        sta Level
        lda #0
        sta ScoreHiBCD
        sta ScoreLoBCD
        jmp StartLevel

UpdatePlaying:
        jsr UpdateTimer

        dec PhaseTimer
        bne CheckMovement
        jsr ToggleLight

CheckMovement:
        ; Any joystick direction while the doll is watching is fatal. During a
        ; green light, Up advances and Left/Right steer around obstacles.
        lda SWCHA
        and #%11110000
        cmp #%11110000
        beq UpdateDone

        lda LightState
        beq SafeMovement
        jsr KillPlayer
        rts

SafeMovement:
        lda SWCHA
        and #%00010000
        bne CheckMoveLeft
        lda PlayerY
        beq FinishLevel
        dec PlayerY
        jsr CheckObstacleCollision
        bcc CheckFinish
        inc PlayerY
        bcs CheckMoveLeft
CheckFinish:
        lda PlayerY
        beq FinishLevel

CheckMoveLeft:
        lda SWCHA
        and #%01000000
        bne CheckMoveRight
        lda PlayerX
        cmp #PLAYER_MIN_X
        beq CheckMoveRight
        dec PlayerX
        jsr CheckObstacleCollision
        bcc CheckMoveRight
        inc PlayerX

CheckMoveRight:
        lda SWCHA
        and #%10000000
        bne UpdateDone
        lda PlayerX
        cmp #PLAYER_MAX_X
        beq UpdateDone
        inc PlayerX
        jsr CheckObstacleCollision
        bcc UpdateDone
        dec PlayerX
        rts

FinishLevel:
        jsr CompleteLevel
UpdateDone:
        rts

StartLevel:
        lda #$00
        sta NUSIZ0             ; Restore the normal-width gameplay octopus.
        sta VDELP0             ; Leave no delayed title-text graphics active.
        sta VDELP1
        sta GRP0
        sta GRP1
        lda #$05
        sta NUSIZ1             ; One double-width doll, not three close copies.
        lda #STATE_PLAY
        sta GameState
        lda #PLAYER_START_Y
        sta PlayerY
        lda #PLAYER_START_X
        sta PlayerX
        lda #LIGHT_GREEN
        sta LightState
        lda #$99
        sta TimerLoBCD
        lda #$09
        sta TimerHiBCD
        lda #4
        sta TimerSubframe
        lda #1
        sta TimerSkipTick
        lda #0
        sta StateTimer
        jsr PlaceObstacles
        jsr LoadPhaseTimer
        jsr BuildHUD
        rts

; Levels 2, 4, 6, and 8 receive one object in each of three separated vertical
; bands. X coordinates span 40-103, safely inside the arena's middle 60%, and
; every coordinate is regenerated once when the round begins.
PlaceObstacles:
        lda Level
        and #$01
        bne NoLevelObstacles
        lda Level
        cmp #9
        bcs NoLevelObstacles
        lda #1
        sta ObstaclesActive

        jsr RandomObstacleX
        sta ObstacleX
        jsr NextRandom
        and #$0F
        clc
        adc #32
        sta ObstacleY

        jsr RandomObstacleX
        sta ObstacleX+1
        jsr NextRandom
        and #$0F
        clc
        adc #64
        sta ObstacleY+1

        jsr RandomObstacleX
        sta ObstacleX+2
        jsr NextRandom
        and #$0F
        clc
        adc #96
        sta ObstacleY+2
        rts

NoLevelObstacles:
        lda #0
        sta ObstaclesActive
        lda #$FF               ; Keeps all three display checks offscreen.
        sta ObstacleY
        sta ObstacleY+1
        sta ObstacleY+2
        rts

RandomObstacleX:
        jsr NextRandom
        and #$3F
        clc
        adc #40
        rts

; Carry returns set when the player's 8x12 rectangle overlaps any obstacle.
; The object coordinates are parallel arrays, allowing one compact AABB loop.
CheckObstacleCollision:
        lda ObstaclesActive
        beq NoObstacleCollision
        ldx #0
CheckNextObstacle:
        lda PlayerY
        clc
        adc #PLAYER_HEIGHT
        cmp ObstacleY,x
        bcc TryNextObstacle
        beq TryNextObstacle

        lda ObstacleY,x
        clc
        adc ObstacleHeights,x
        cmp PlayerY
        bcc TryNextObstacle
        beq TryNextObstacle

        lda PlayerX
        clc
        adc #PLAYER_WIDTH
        cmp ObstacleX,x
        bcc TryNextObstacle
        beq TryNextObstacle

        lda ObstacleX,x
        clc
        adc #PLAYER_WIDTH
        cmp PlayerX
        bcc TryNextObstacle
        beq TryNextObstacle
        sec
        rts

TryNextObstacle:
        inx
        cpx #3
        bne CheckNextObstacle
NoObstacleCollision:
        clc
        rts

ToggleLight:
        lda LightState
        eor #$01
        sta LightState
        jsr LoadPhaseTimer

        lda LightState
        beq GreenLightCue
        lda #SOUND_RED_CUE
        sta SoundKind
        lda #7
        sta SoundTimer
        rts
GreenLightCue:
        lda #SOUND_GREEN_CUE
        sta SoundKind
        lda #5
        sta SoundTimer
        rts

LoadPhaseTimer:
        ; Level 1 ranges from 80-111 frames. Each level removes six frames,
        ; reaching 32-63 frames at level 9.
        lda Level
        asl
        sta Temp                ; level * 2
        asl                     ; level * 4
        clc
        adc Temp                ; level * 6
        sta Temp
        lda #86
        sec
        sbc Temp
        sta Temp

        jsr NextRandom
        and #$1F
        clc
        adc Temp
        sta PhaseTimer
        rts

NextRandom:
        lda RandomSeed
        lsr
        bcc RandomReady
        eor #$B8
RandomReady:
        bne RandomNonzero
        lda #$A5
RandomNonzero:
        sta RandomSeed
        rts

UpdateTimer:
        ; Five tick slots every nine NTSC frames would produce 1000 ticks in
        ; 1800 frames. Skip the first slot so 999 reaches zero on frame 1800,
        ; exactly 30 seconds at 60 frames per second.
        inc TimerSubframe
        lda TimerSubframe
        cmp #9
        bcc TimerPhaseReady
        lda #0
        sta TimerSubframe
TimerPhaseReady:
        cmp #5
        bcs TimerDone

        lda TimerSkipTick
        beq TimerCanDecrement
        dec TimerSkipTick
        rts
TimerCanDecrement:

        lda TimerHiBCD
        ora TimerLoBCD
        beq TimerDone

        sed
        sec
        lda TimerLoBCD
        sbc #$01
        sta TimerLoBCD
        lda TimerHiBCD
        sbc #$00
        sta TimerHiBCD
        cld
        jsr BuildTimerHUD
TimerDone:
        rts

CompleteLevel:
        ; Award 100 points plus every point left on the round timer. The four
        ; digit display saturates at 9999 if level nine is replayed repeatedly.
        sed
        clc
        lda ScoreLoBCD
        adc TimerLoBCD
        sta ScoreLoBCD
        lda ScoreHiBCD
        adc TimerHiBCD
        bcs SaturateScore
        clc
        adc #$01              ; Guaranteed 100-point completion award.
        bcs SaturateScore
        sta ScoreHiBCD
        cld
        jmp ScoreAwarded
SaturateScore:
        lda #$99
        sta ScoreHiBCD
        sta ScoreLoBCD
        cld
ScoreAwarded:
        lda #STATE_CLEAR
        sta GameState
        lda #LIGHT_GREEN
        sta LightState
        lda #90
        sta StateTimer
        lda #SOUND_CLEAR
        sta SoundKind
        lda #40
        sta SoundTimer
        jsr BuildHUD
        rts

KillPlayer:
        lda #STATE_DEAD
        sta GameState
        lda #LIGHT_RED
        sta LightState
        lda #SOUND_GUNSHOT
        sta SoundKind
        lda #32
        sta SoundTimer
        rts

; -----------------------------------------------------------------------------
; Sound
; -----------------------------------------------------------------------------

UpdateSound:
        lda GameState
        cmp #STATE_TITLE
        bne UpdateEffectSound
        jmp UpdateTitleMusic

UpdateEffectSound:
        lda SoundTimer
        beq SilenceAudio
        dec SoundTimer

        lda SoundKind
        cmp #SOUND_GUNSHOT
        beq GunshotAudio
        cmp #SOUND_CLEAR
        beq ClearAudio
        cmp #SOUND_RED_CUE
        beq RedCueAudio

        ; Green cue, a short high tone.
        lda #4
        sta AUDC0
        lda #6
        sta AUDF0
        lda #6
        sta AUDV0
        rts

RedCueAudio:
        lda #4
        sta AUDC0
        lda #18
        sta AUDF0
        lda #7
        sta AUDV0
        rts

ClearAudio:
        lda #4
        sta AUDC0
        lda SoundTimer
        lsr
        and #$0F
        sta AUDF0
        lda #10
        sta AUDV0
        rts

GunshotAudio:
        lda #8                  ; Polynomial noise.
        sta AUDC0
        lda SoundTimer
        and #$1F
        sta AUDF0
        lda #15
        sta AUDV0
        rts

SilenceAudio:
        lda #0
        sta AUDV0
        sta AUDV1
        sta SoundKind
        rts

; A compact original title cue derived from broad traits measured in the
; supplied reference: a suspended high tone and short descending answers. The
; former steady percussion channel is intentionally silent.
UpdateTitleMusic:
        inc TitleMusicFrame
        lda TitleMusicFrame
        cmp #12
        bcc PlayTitleMusicStep
        lda #0
        sta TitleMusicFrame
        inc TitleMusicStep
        lda TitleMusicStep
        cmp #30
        bcc PlayTitleMusicStep
        lda #0
        sta TitleMusicStep

PlayTitleMusicStep:
        lda #0
        sta AUDV1               ; No repeating bass-drum pulse.
        ldx TitleMusicStep
        lda TitleMelody,x
        cmp #$FF
        beq TitleMelodyRest
        sta AUDF0
        lda #4                  ; Bright pure-tone voice.
        sta AUDC0
        lda #7
        sta AUDV0
        rts
TitleMelodyRest:
        lda #0
        sta AUDV0
        rts

; -----------------------------------------------------------------------------
; Display helpers
; -----------------------------------------------------------------------------

SetObjectColors:
        lda #COLOR_BLACK
        sta COLUBK
        lda #COLOR_OCTO_GREEN
        sta COLUP0

        lda GameState
        cmp #STATE_DEAD
        bne NotDeadColors
        lda #COLOR_DARK_RED
        sta COLUBK
        lda #COLOR_RED
        sta COLUP0
        lda #COLOR_DOLL_FACE
        sta COLUP1
        rts
NotDeadColors:
        cmp #STATE_CLEAR
        bne PlayingColors
        lda #COLOR_DARK_GREEN
        sta COLUBK
        lda #COLOR_GOLD
        sta COLUP0
        lda #COLOR_DOLL_BACK
        sta COLUP1
        rts
PlayingColors:
        lda LightState
        beq DollBackColor
        lda #COLOR_DOLL_FACE
        sta COLUP1
        rts
DollBackColor:
        lda #COLOR_DOLL_BACK
        sta COLUP1
        rts

; Return the current arena color in A without changing a TIA register. The
; kernel applies it immediately after WSYNC to avoid a partial-color scanline.
LoadLaneColor:
        lda GameState
        cmp #STATE_DEAD
        beq LaneRed
        cmp #STATE_CLEAR
        beq LaneGold
        lda LightState
        bne LaneRed
        lda #COLOR_GREEN
        rts
LaneRed:
        lda #COLOR_RED
        rts
LaneGold:
        lda #COLOR_GOLD
        rts

; Position TIA object X (0 = P0, 1 = P1) at horizontal coordinate A.
PositionObject:
        sta WSYNC
        sec
PositionLoop:
        sbc #15
        bcs PositionLoop
        eor #7
        asl
        asl
        asl
        asl
        sta HMP0,x
        sta RESP0,x
        rts

; -----------------------------------------------------------------------------
; HUD generation
; -----------------------------------------------------------------------------

BuildHUD:
        jsr BuildScoreHUD
        jmp BuildTimerHUD

BuildScoreHUD:
        lda ScoreHiBCD
        lsr
        lsr
        lsr
        lsr
        jsr DigitOffset
        sta Digit0Index

        lda ScoreHiBCD
        and #$0F
        jsr DigitOffset
        sta Digit1Index

        lda ScoreLoBCD
        lsr
        lsr
        lsr
        lsr
        jsr DigitOffset
        sta Digit2Index

        lda ScoreLoBCD
        and #$0F
        jsr DigitOffset
        sta Digit3Index

        ldx #0
BuildScoreRow:
        lda #0
        sta ScorePF0,x

        ldy Digit0Index
        lda DigitFont,y
        asl
        asl
        asl
        asl
        sta Temp
        inc Digit0Index

        ldy Digit1Index
        lda DigitFont,y
        ora Temp
        sta ScorePF1,x
        inc Digit1Index

        ldy Digit2Index
        lda DigitFont,y
        tay
        lda Reverse3,y
        asl
        sta Temp
        inc Digit2Index

        ldy Digit3Index
        lda DigitFont,y
        tay
        lda Reverse3,y
        asl
        asl
        asl
        asl
        asl
        ora Temp
        sta ScorePF2,x
        inc Digit3Index

        inx
        cpx #HUD_ROWS
        bne BuildScoreRow
        rts

BuildTimerHUD:
        lda TimerHiBCD
        and #$0F
        jsr DigitOffset
        sta Digit0Index

        lda TimerLoBCD
        lsr
        lsr
        lsr
        lsr
        jsr DigitOffset
        sta Digit1Index

        lda TimerLoBCD
        and #$0F
        jsr DigitOffset
        sta Digit2Index

        ldx #0
BuildTimerRow:
        lda #0
        sta TimerPF0,x

        ldy Digit0Index
        lda DigitFont,y
        asl
        asl
        asl
        asl
        asl
        sta Temp
        inc Digit0Index

        ldy Digit1Index
        lda DigitFont,y
        asl
        ora Temp
        sta TimerPF1,x
        inc Digit1Index

        ldy Digit2Index
        lda DigitFont,y
        tay
        lda Reverse3,y
        sta TimerPF2,x
        inc Digit2Index

        inx
        cpx #HUD_ROWS
        bne BuildTimerRow
        rts

; Build the fine-text portion of the ending in the six display strips. Rows
; 5-9 contain a wider FINAL SCORE label, row zero is blank, and rows 1-4 hold
; the centered five-digit value. The leading digit is always zero because
; gameplay saturates at 9999.
BuildVictoryText:
        lda #0
        sta DisplayText0
        sta DisplayText1
        sta DisplayText2
        sta DisplayText3
        sta DisplayText4
        sta DisplayText5

        lda #4
        sta Digit0Index

        lda ScoreHiBCD
        lsr
        lsr
        lsr
        lsr
        jsr DigitOffset
        clc
        adc #4
        sta Digit1Index

        lda ScoreHiBCD
        and #$0F
        jsr DigitOffset
        clc
        adc #4
        sta Digit2Index

        lda ScoreLoBCD
        lsr
        lsr
        lsr
        lsr
        jsr DigitOffset
        clc
        adc #4
        sta Digit3Index

        lda ScoreLoBCD
        and #$0F
        jsr DigitOffset
        clc
        adc #4
        sta PhaseTimer

        ldx #0
BuildVictoryRow:
        lda SurvivedText0,x
        sta DisplayText0+10,x
        lda SurvivedText1,x
        sta DisplayText1+10,x
        lda SurvivedText2,x
        sta DisplayText2+10,x
        lda SurvivedText3,x
        sta DisplayText3+10,x
        lda SurvivedText4,x
        sta DisplayText4+10,x
        lda SurvivedText5,x
        sta DisplayText5+10,x

        lda FinalLabel0,x
        sta DisplayText0+5,x
        lda FinalLabel1,x
        sta DisplayText1+5,x
        lda FinalLabel2,x
        sta DisplayText2+5,x
        lda FinalLabel3,x
        sta DisplayText3+5,x
        lda FinalLabel4,x
        sta DisplayText4+5,x
        lda FinalLabel5,x
        sta DisplayText5+5,x

        cpx #4
        beq VictoryScoreRowDone

        lda #0
        sta DisplayText0+1,x
        sta DisplayText1+1,x
        sta DisplayText2+1,x
        sta DisplayText3+1,x
        sta DisplayText4+1,x
        sta DisplayText5+1,x

        ; Pack five 3x5 digits with a one-pixel gap into the center twenty
        ; pixels. Two digits fit in each byte as ddd0ddd0.
        ldy Digit0Index
        lda DigitFont,y
        asl
        asl
        asl
        asl
        asl
        sta DisplayText2+1,x
        dec Digit0Index

        ldy Digit1Index
        lda DigitFont,y
        asl
        ora DisplayText2+1,x
        sta DisplayText2+1,x
        dec Digit1Index

        ldy Digit2Index
        lda DigitFont,y
        asl
        asl
        asl
        asl
        asl
        sta DisplayText3+1,x
        dec Digit2Index

        ldy Digit3Index
        lda DigitFont,y
        asl
        ora DisplayText3+1,x
        sta DisplayText3+1,x
        dec Digit3Index

        ldy PhaseTimer
        lda DigitFont,y
        asl
        asl
        asl
        asl
        asl
        sta DisplayText4+1,x
        dec PhaseTimer

        ; Omit the second font row to retain a readable four-row score.
        cpx #2
        bne VictoryScoreRowDone
        dec Digit0Index
        dec Digit1Index
        dec Digit2Index
        dec Digit3Index
        dec PhaseTimer

VictoryScoreRowDone:
        inx
        cpx #HUD_ROWS
        beq VictoryTextBuilt
        jmp BuildVictoryRow
VictoryTextBuilt:
        rts

DigitOffset:
        sta Temp
        asl
        asl
        clc
        adc Temp
        rts

; -----------------------------------------------------------------------------
; Graphics and digit data
; -----------------------------------------------------------------------------

TreeSprite:
        byte %00011000
        byte %00111100
        byte %01111110
        byte %11111111
        byte %01111110
        byte %00111100
        byte %00011000
        byte %00011000
        byte %00011000
        byte %00011000
        byte %00111100
        byte %00111100

ObstacleHeights:
        byte TREE_HEIGHT,BOULDER_HEIGHT,BOULDER_HEIGHT

DollBackSprite:
        byte %00111100
        byte %01111110
        byte %11111111
        byte %11111111
        byte %11111111
        byte %01111110
        byte %00111100
        byte %01000010

DollFaceSprite:
        byte %00111100
        byte %01111110
        byte %11011011
        byte %11111111
        byte %01111111
        byte %00111111
        byte %00100100
        byte %01000010

Reverse3:
        byte 0,4,2,6,1,5,3,7

; Three-bit-wide, five-row digits, stored digit-major.
DigitFont:
        byte 7,5,5,5,7       ; 0
        byte 2,6,2,2,7       ; 1
        byte 7,1,7,4,7       ; 2
        byte 7,1,7,1,7       ; 3
        byte 5,5,7,1,1       ; 4
        byte 7,4,7,1,7       ; 5
        byte 7,4,7,5,7       ; 6
        byte 7,1,1,1,1       ; 7
        byte 7,5,7,5,7       ; 8
        byte 7,5,7,1,7       ; 9

; Original title cue, 30 steps at 12 frames per step (6 seconds). $FF is a
; rest. TIA divisors use 2n+1 to lower the earlier melody by one octave while
; preserving its uneasy drone and descending replies.
TitleMelody:
        byte 31,31,31,31, 31,31,31,31, 31,31,31,31
        byte 25,25,31,31, 31,35,35,41, 35,35,31,31
        byte 35,39,25,25,25,$FF

; "YOU SURVIVED!" in a centered variable-width 3x5 font. Rows are stored
; bottom-up for the title-style six-copy player kernel.
SurvivedText0:
        byte $23,$24,$64,$94,$93
SurvivedText1:
        byte $18,$A4,$A4,$A4,$24
SurvivedText2:
        byte $77,$15,$75,$45,$75
SurvivedText3:
        byte $52,$55,$65,$55,$65
SurvivedText4:
        byte $49,$55,$55,$55,$55
SurvivedText5:
        byte $D9,$14,$95,$15,$D9

; "FINAL SCORE:" in a centered variable-width 3x5 font. Rows remain
; bottom-up for the six-copy player kernel.
FinalLabel0:
        byte $85,$85,$E5,$85,$F5
FinalLabel1:
        byte $29,$29,$6F,$A9,$26
FinalLabel2:
        byte $7B,$40,$41,$42,$41
FinalLabel3:
        byte $8E,$50,$90,$10,$CE
FinalLabel4:
        byte $64,$95,$97,$94,$67
FinalLabel5:
        byte $BC,$21,$38,$A1,$3C

        include "src/title_scene.inc"

; Physical-row map for the enlarged victory display. The table is read from
; index 69 down to zero: six scanlines per headline row, five blank lines,
; three per label row, four blank lines, and four per score row.
VictoryRowMap:
        byte 1,1,1,1, 2,2,2,2, 3,3,3,3, 4,4,4,4
        byte 0,0,0,0
        byte 5,5,5, 6,6,6, 7,7,7, 8,8,8, 9,9,9
        byte 0,0,0,0,0
        byte 10,10,10,10,10,10, 11,11,11,11,11,11
        byte 12,12,12,12,12,12, 13,13,13,13,13,13
        byte 14,14,14,14,14,14

; A half-page makes every non-negative out-of-range player row read as zero.
; Negative differences are rejected before indexing, leaving enough beam time
; for three independently positioned obstacles.
        align 128
OctoLineTable:
        byte %00111100
        byte %01111110
        byte %11111111
        byte %11011011
        byte %11111111
        byte %01111110
        byte %00111100
        byte %01111110
        byte %11011011
        byte %10011001
        byte %01011010
        byte %10100101
        ds 116,0

; 6507 vectors. The 2600 only uses RESET, but all vectors point somewhere safe.
        org $FFFA
        word Reset
        word Reset
        word Reset

        end
