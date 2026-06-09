# Jetpack Compose / KMP Reference

## Project Setup

Android Studio → New Project → Empty Activity (Compose). Requires `compileSdk 35+`, Kotlin 2.0+.

```kotlin
// build.gradle.kts (app)
dependencies {
  val composeBom = platform("androidx.compose:compose-bom:2024.09.00")
  implementation(composeBom)
  implementation("androidx.compose.ui:ui")
  implementation("androidx.compose.material3:material3")
  implementation("androidx.compose.animation:animation")          // shared elements
  implementation("androidx.compose.ui:ui-tooling-preview")
  implementation("androidx.navigation:navigation-compose:2.8.0")  // SharedTransitionLayout
  implementation("androidx.lifecycle:lifecycle-viewmodel-compose:2.8.4")
  implementation("androidx.datastore:datastore-preferences:1.1.1") // onboarding state
  debugImplementation("androidx.compose.ui:ui-tooling")
}
```

---

## Composable Architecture

Every UI element is a `@Composable` function. Three rules:

1. **Composables only call composables**
2. **Idempotent** — same inputs always produce the same UI
3. **No side effects in the body** — use `LaunchedEffect`, `SideEffect`, `DisposableEffect`

```kotlin
@Composable
fun ItemCard(
  item: Item,
  onClick: () -> Unit,   // events go up
) {
  NeuBrutCard(onClick = onClick) {   // see Neubrut Primitives below
    Column(Modifier.padding(16.dp)) {
      Text(item.title, style = AppType.cardTitle)
      Text(item.subtitle, style = AppType.body)
    }
  }
}
```

---

## State Hoisting

**State goes up, events go down.** Don't bury state inside a composable unless it's truly local.

```kotlin
// ❌ Trapped — not reusable, not testable
@Composable
fun SearchBar() {
  var query by remember { mutableStateOf("") }
  TextField(value = query, onValueChange = { query = it })
}

// ✓ Hoisted
@Composable
fun SearchBar(query: String, onQueryChange: (String) -> Unit) {
  TextField(value = query, onValueChange = onQueryChange)
}
```

---

## Neubrut Primitives

Define these once and use everywhere — this is how the token system becomes consistent:

```kotlin
object NeuBrut {
  // Tokens
  val Ink = Color(0xFF0A0A0A)
  val InkDark = Color(0xFFF5F5F5)
  val Bg = Color(0xFFFAFAFA)
  val BgDark = Color(0xFF0F0F0F)
  // Set your accent once here:
  val Accent = Color(0xFFFFD60A)  // e.g. Volt Yellow

  val BorderWidth = 2.5.dp
  val ShadowOffset = 4.dp
  val Radius = 8.dp
}

// Hard shadow modifier (the signature move)
fun Modifier.hardShadow(
  offset: Dp = NeuBrut.ShadowOffset,
  color: Color = NeuBrut.Ink,
): Modifier = this
  .offset(x = 0.dp, y = 0.dp)  // caller controls translate for press anim
  .drawBehind {
    drawRect(
      color = color,
      topLeft = Offset(offset.toPx(), offset.toPx()),
      size = size,
    )
  }

// Neubrut card primitive
@Composable
fun NeuBrutCard(
  onClick: (() -> Unit)? = null,
  accentFill: Boolean = false,
  modifier: Modifier = Modifier,
  content: @Composable ColumnScope.() -> Unit,
) {
  val interactionSource = remember { MutableInteractionSource() }
  val isPressed by interactionSource.collectIsPressedAsState()

  // Spring-animated press state
  val offsetX by animateDpAsState(
    targetValue = if (isPressed) 2.dp else 0.dp,
    animationSpec = NeuSpring.snap,
    label = "pressX",
  )
  val offsetY by animateDpAsState(
    targetValue = if (isPressed) 2.dp else 0.dp,
    animationSpec = NeuSpring.snap,
    label = "pressY",
  )
  val shadowOffset by animateDpAsState(
    targetValue = if (isPressed) 1.dp else NeuBrut.ShadowOffset,
    animationSpec = NeuSpring.snap,
    label = "shadow",
  )

  val ink = if (isSystemInDarkTheme()) NeuBrut.InkDark else NeuBrut.Ink
  val bg = if (accentFill) NeuBrut.Accent
  else if (isSystemInDarkTheme()) NeuBrut.BgDark else NeuBrut.Bg

  Column(
    modifier = modifier
      .offset(x = offsetX, y = offsetY)
      .hardShadow(offset = shadowOffset, color = ink)
      .border(NeuBrut.BorderWidth, ink, RoundedCornerShape(NeuBrut.Radius))
      .background(bg, RoundedCornerShape(NeuBrut.Radius))
      .then(if (onClick != null) Modifier.clickable(interactionSource, null, onClick = onClick) else Modifier),
    content = content,
  )
}

// Neubrut button
@Composable
fun NeuBrutButton(
  text: String,
  onClick: () -> Unit,
  modifier: Modifier = Modifier,
  isPrimary: Boolean = true,
) {
  val haptic = LocalHapticFeedback.current
  NeuBrutCard(
    onClick = { haptic.performHapticFeedback(HapticFeedbackType.TextHandleMove); onClick() },
    accentFill = isPrimary,
    modifier = modifier,
  ) {
    Text(
      text = text.uppercase(),
      style = AppType.buttonLabel,
      modifier = Modifier
        .fillMaxWidth()
        .padding(horizontal = 20.dp, vertical = 14.dp),
      textAlign = TextAlign.Center,
    )
  }
}
```

---

## 1. Spring Physics

**Rule: replace every `tween()` in your codebase with a spring. Use `tween` only for progress indicators and infinite loops.**

### Spring Config Reference

```kotlin
object NeuSpring {
  // Snappy — tabs, pressed states, immediate feedback
  val snap = spring<Float>(
    dampingRatio = Spring.DampingRatioNoBouncy,
    stiffness = Spring.StiffnessHigh,  // 10000
  )

  // Bounce — cards appearing, FAB, list items entering
  val bounce = spring<Float>(
    dampingRatio = Spring.DampingRatioMediumBouncy,  // 0.5
    stiffness = Spring.StiffnessMedium,              // 1500
  )

  // Float — drawers, bottom sheets, modals
  val float = spring<Float>(
    dampingRatio = Spring.DampingRatioLowBouncy,  // 0.75
    stiffness = Spring.StiffnessMediumLow,        // 400
  )
}
```

| Config | DampingRatio | Stiffness | Use For |
|---|---|---|---|
| `snap` | NoBouncy (1.0) | High (10000) | Tab switch, pressed state |
| `bounce` | MediumBouncy (0.5) | Medium (1500) | Card enter, scale |
| `float` | LowBouncy (0.75) | MediumLow (400) | Sheet entry, drawer |

### Usage

```kotlin
// Scale on press — use snap for immediate physical feel
val scale by animateFloatAsState(
  targetValue = if (isPressed) 0.96f else 1f,
  animationSpec = NeuSpring.snap,
  label = "scale",
)

// Card entering a list — stagger with bounce
val visible = remember { mutableStateOf(false) }
LaunchedEffect(Unit) { delay(index * 40L); visible.value = true }
AnimatedVisibility(
  visible = visible.value,
  enter = fadeIn(NeuSpring.bounce) + scaleIn(NeuSpring.bounce, initialScale = 0.92f),
) { ItemCard(item) }

// Sheet / modal entry — float feels natural
AnimatedVisibility(
  visible = sheetVisible,
  enter = slideInVertically(NeuSpring.float) { it },
  exit = slideOutVertically(NeuSpring.float) { it },
) { BottomSheet() }
```

### Migration Checklist
- [ ] `animateFloatAsState` / `animateDpAsState` — replace `tween()` with spring
- [ ] `AnimatedVisibility` enter/exit — replace `tween` specs with spring
- [ ] `animateContentSize` — `animateContentSize(NeuSpring.bounce)`
- [ ] Explicit `Animatable` uses — call `animateTo(target, NeuSpring.bounce)`

---

## 2. Skeleton Screens

Show skeleton screens when `uiState.isLoading == true`. Never show a spinner for list/card content.

### Shimmer Composable

```kotlin
@Composable
fun ShimmerBrush(
  widthPx: Float = 1000f,
): Brush {
  val ink = if (isSystemInDarkTheme()) NeuBrut.InkDark else NeuBrut.Ink
  val transition = rememberInfiniteTransition(label = "shimmer")
  val offsetX by transition.animateFloat(
    initialValue = -widthPx,
    targetValue = widthPx * 2,
    animationSpec = infiniteRepeatable(
      animation = tween(durationMillis = 1200, easing = LinearEasing),
      repeatMode = RepeatMode.Restart,
    ),
    label = "shimmer_x",
  )
  return Brush.linearGradient(
    colors = listOf(
      ink.copy(alpha = 0.06f),
      ink.copy(alpha = 0.14f),
      ink.copy(alpha = 0.06f),
    ),
    start = Offset(offsetX, 0f),
    end = Offset(offsetX + widthPx, 0f),
  )
}

// Skeleton block — use in place of real content shapes
@Composable
fun SkeletonBlock(
  modifier: Modifier = Modifier,
  height: Dp = 16.dp,
  width: Dp = Dp.Unspecified,
) {
  val ink = if (isSystemInDarkTheme()) NeuBrut.InkDark else NeuBrut.Ink
  val brush = ShimmerBrush()
  Box(
    modifier = modifier
      .then(if (width != Dp.Unspecified) Modifier.width(width) else Modifier.fillMaxWidth())
      .height(height)
      .border(1.dp, ink.copy(alpha = 0.15f), RoundedCornerShape(NeuBrut.Radius))
      .background(brush, RoundedCornerShape(NeuBrut.Radius))
  )
}
```

### Card Skeleton (matches NeuBrutCard proportions)

```kotlin
@Composable
fun ItemCardSkeleton() {
  val ink = if (isSystemInDarkTheme()) NeuBrut.InkDark else NeuBrut.Ink
  Column(
    modifier = Modifier
      .fillMaxWidth()
      .hardShadow()
      .border(NeuBrut.BorderWidth, ink, RoundedCornerShape(NeuBrut.Radius))
      .background(if (isSystemInDarkTheme()) NeuBrut.BgDark else NeuBrut.Bg, RoundedCornerShape(NeuBrut.Radius))
      .padding(16.dp),
    verticalArrangement = Arrangement.spacedBy(8.dp),
  ) {
    SkeletonBlock(height = 20.dp, width = 160.dp)  // title
    SkeletonBlock(height = 14.dp, width = 240.dp)  // subtitle
    SkeletonBlock(height = 14.dp, width = 200.dp)  // subtitle line 2
  }
}

// Wiring into screen:
@Composable
fun ItemListScreen(viewModel: ItemViewModel = viewModel()) {
  val state by viewModel.uiState.collectAsStateWithLifecycle()

  LazyColumn(contentPadding = PaddingValues(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
    if (state.isLoading) {
      items(5) { ItemCardSkeleton() }  // show 5 placeholder cards
    } else {
      items(state.items, key = { it.id }) { item ->
        ItemCard(item = item)
      }
    }
  }
}
```

---

## 3. Haptics

### Install

```kotlin
// Compose's LocalHapticFeedback covers basic events on Android.
// For richer patterns (success, error, heavy impact), use the Vibrator API.
implementation("androidx.core:core-ktx:1.13.1")
```

### Event Map — Use These Consistently Across the App

```kotlin
object AppHaptics {
  // Call from composables via LocalHapticFeedback
  @Composable
  fun rememberHaptic(): HapticFeedback = LocalHapticFeedback.current
}

// ── Event → Haptic type ───────────────────────────────────────────────────
// Button tap (standard)      → TextHandleMove (light)
// Toggle / checkbox          → LongPress (medium)
// Tab bar switch             → TextHandleMove (light)
// Pull-to-refresh triggered  → LongPress (medium)
// Destructive confirm        → LongPress (heavy — wire via Vibrator)
// Success                    → custom success pattern (see below)
// Error / validation fail    → custom error pattern (see below)
// ─────────────────────────────────────────────────────────────────────────
```

### Rich Haptic Patterns (Android Vibrator API)

```kotlin
// HapticUtil.kt
import android.content.Context
import android.os.Build
import android.os.VibrationEffect
import android.os.VibratorManager
import androidx.core.content.getSystemService

object HapticUtil {
  fun success(context: Context) {
    vibrate(context, longArrayOf(0, 40, 30, 80))  // tap, pause, tap (longer)
  }

  fun error(context: Context) {
    vibrate(context, longArrayOf(0, 80, 40, 80, 40, 80))  // three rapid pulses
  }

  fun heavyImpact(context: Context) {
    vibrate(context, longArrayOf(0, 120))
  }

  private fun vibrate(context: Context, pattern: LongArray) {
    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
      val vm = context.getSystemService<VibratorManager>()
      vm?.defaultVibrator?.vibrate(VibrationEffect.createWaveform(pattern, -1))
    } else {
      @Suppress("DEPRECATION")
      val vib = context.getSystemService(Context.VIBRATOR_SERVICE) as android.os.Vibrator
      vib.vibrate(pattern, -1)
    }
  }
}
```

### Wiring Haptics Into Your Composables

```kotlin
@Composable
fun ActionButton(
  text: String,
  onClick: () -> Unit,
  hapticType: HapticEventType = HapticEventType.Tap,
) {
  val haptic = LocalHapticFeedback.current
  val context = LocalContext.current

  NeuBrutButton(
    text = text,
    onClick = {
      when (hapticType) {
        HapticEventType.Tap -> haptic.performHapticFeedback(HapticFeedbackType.TextHandleMove)
        HapticEventType.Toggle -> haptic.performHapticFeedback(HapticFeedbackType.LongPress)
        HapticEventType.Success -> HapticUtil.success(context)
        HapticEventType.Error -> HapticUtil.error(context)
        HapticEventType.Destructive -> HapticUtil.heavyImpact(context)
      }
      onClick()
    },
  )
}

enum class HapticEventType { Tap, Toggle, Success, Error, Destructive }
```

---

## 4. Empty & Error States

These must be **designed**, not afterthoughts. A blank screen or a gray "No items found" is a missed moment of trust-building.

### Structure (Neubrut Style)

```kotlin
@Composable
fun EmptyState(
  headline: String,
  body: String,
  ctaText: String,
  onCta: () -> Unit,
  modifier: Modifier = Modifier,
  // Optional: pass a simple geometric composable as illustration
  illustration: (@Composable () -> Unit)? = null,
) {
  Column(
    modifier = modifier
      .fillMaxWidth()
      .padding(horizontal = 32.dp, vertical = 48.dp),
    horizontalAlignment = Alignment.CenterHorizontally,
    verticalArrangement = Arrangement.spacedBy(16.dp),
  ) {
    illustration?.invoke()

    Text(headline, style = AppType.screenTitle, textAlign = TextAlign.Center)
    Text(body, style = AppType.body.copy(color = ..., alpha = 0.7f), textAlign = TextAlign.Center)
    Spacer(Modifier.height(8.dp))
    NeuBrutButton(text = ctaText, onClick = onCta, modifier = Modifier.fillMaxWidth())
  }
}
```

### Copy Guidelines

These are exact patterns — use them, don't soften them:

| State | ❌ Weak copy | ✓ Neubrut copy |
|---|---|---|
| Empty list | "It looks like you haven't added anything yet." | "Nothing here yet." |
| No results | "Your search returned no results." | "No matches for that." |
| Network error | "Unable to complete your request." | "Couldn't connect. Check your connection." |
| Server error | "Something went wrong." | "Something broke on our end. We're on it." |
| Permission denied | "You have not granted the required permissions." | "We need permission to do that." |
| Not found | "The item you requested does not exist." | "This doesn't exist anymore." |

**CTA copy:** verb + object. "Add your first workout", "Try again", "Go back", "Retry". Never "Get started" or "Click here".

### Neubrut Geometric Illustration Pattern

Instead of stock sad-face icons, use a simple geometric shape built in Canvas:

```kotlin
@Composable
fun EmptyBoxIllustration(size: Dp = 80.dp) {
  val ink = if (isSystemInDarkTheme()) NeuBrut.InkDark else NeuBrut.Ink
  Canvas(Modifier.size(size)) {
    // Outer box (hard shadow + border — matches card aesthetic)
    val box = Rect(size.toPx() * 0.1f, size.toPx() * 0.1f, size.toPx() * 0.7f, size.toPx() * 0.7f)
    // Shadow
    drawRect(color = ink, topLeft = Offset(box.left + 6.dp.toPx(), box.top + 6.dp.toPx()), size = box.size)
    // Fill
    drawRect(color = NeuBrut.Accent, topLeft = box.topLeft, size = box.size)
    // Border
    drawRect(color = ink, topLeft = box.topLeft, size = box.size, style = Stroke(NeuBrut.BorderWidth.toPx()))
    // Question mark or X in center — draw as simple lines
  }
}
```

### Error State

For network/server errors, include a retry mechanism:

```kotlin
@Composable
fun ErrorState(
  message: String,
  onRetry: () -> Unit,
) {
  EmptyState(
    headline = message,
    body = "Pull down to refresh or tap retry.",
    ctaText = "Retry",
    onCta = onRetry,
  )
}

// In your screen:
when {
  state.isLoading -> repeat(5) { ItemCardSkeleton() }
  state.error != null -> ErrorState(state.error!!, onRetry = viewModel::reload)
  state.items.isEmpty() -> EmptyState(
    headline = "Nothing here yet.",
    body = "Your completed items will appear here.",
    ctaText = "Add your first item",
    onCta = onAddItem,
  )
  else -> ItemList(state.items)
}
```

---

## 5. Shared Element Transitions

Built into Compose 1.7+ via `SharedTransitionLayout`. Requires `navigation-compose:2.8.0+`.

```kotlin
// NavHost must be wrapped in SharedTransitionLayout
@Composable
fun AppNavHost() {
  val navController = rememberNavController()

  SharedTransitionLayout {
    NavHost(navController, startDestination = "list") {

      composable("list") {
        // Pass animatedVisibilityScope so items know when they're visible
        ItemListScreen(
          navController = navController,
          animatedVisibilityScope = this,
          sharedTransitionScope = this@SharedTransitionLayout,
        )
      }

      composable("detail/{id}") { backStackEntry ->
        val id = backStackEntry.arguments?.getString("id") ?: return@composable
        ItemDetailScreen(
          id = id,
          animatedVisibilityScope = this,
          sharedTransitionScope = this@SharedTransitionLayout,
        )
      }
    }
  }
}
```

```kotlin
// List screen — mark the shared element
@Composable
fun ItemListScreen(
  navController: NavController,
  animatedVisibilityScope: AnimatedVisibilityScope,
  sharedTransitionScope: SharedTransitionScope,
) {
  with(sharedTransitionScope) {
    LazyColumn {
      items(items, key = { it.id }) { item ->
        NeuBrutCard(
          modifier = Modifier.sharedElement(
            rememberSharedContentState(key = "card-${item.id}"),
            animatedVisibilityScope = animatedVisibilityScope,
          ),
          onClick = { navController.navigate("detail/${item.id}") },
        ) {
          // The text can also be a shared element for a smoother transition:
          Text(
            item.title,
            modifier = Modifier.sharedElement(
              rememberSharedContentState(key = "title-${item.id}"),
              animatedVisibilityScope = animatedVisibilityScope,
            ),
          )
        }
      }
    }
  }
}

// Detail screen — same keys
@Composable
fun ItemDetailScreen(
  id: String,
  animatedVisibilityScope: AnimatedVisibilityScope,
  sharedTransitionScope: SharedTransitionScope,
) {
  with(sharedTransitionScope) {
    Column(
      modifier = Modifier
        .fillMaxSize()
        .sharedElement(
          rememberSharedContentState(key = "card-$id"),
          animatedVisibilityScope = animatedVisibilityScope,
        )
    ) {
      Text(
        item.title,
        modifier = Modifier.sharedElement(
          rememberSharedContentState(key = "title-$id"),
          animatedVisibilityScope = animatedVisibilityScope,
        ),
      )
      // rest of detail content
    }
  }
}
```

**The transition animation spec defaults to spring.** To override:
```kotlin
Modifier.sharedElement(
  state = rememberSharedContentState("card-$id"),
  animatedVisibilityScope = animatedVisibilityScope,
  boundsTransform = { _, _ -> NeuSpring.float },
)
```

---

## 6. Value-First Onboarding

**Principle:** Let users experience the core value of your app before you ask for anything — signup, permissions, payment.

### The Flow

```
First launch
    ↓
Show the app working (with sample/empty state)
    ↓
User does the core action (creates item, logs workout, etc.)
    ↓
"Save your progress" → signup prompt (soft gate)
    ↓
Feature requires permission → contextual permission request
    ↓
After user sees value → upsell to premium
```

### Guest State with DataStore

```kotlin
// OnboardingRepository.kt
class OnboardingRepository(context: Context) {
  private val prefs = context.dataStorePreferences  // DataStore<Preferences>

  private val HAS_SEEN_ONBOARDING = booleanPreferencesKey("has_seen_onboarding")
  private val IS_SIGNED_UP = booleanPreferencesKey("is_signed_up")
  private val GUEST_ACTION_COUNT = intPreferencesKey("guest_action_count")

  val hasSeenOnboarding: Flow<Boolean> = prefs.data
    .map { it[HAS_SEEN_ONBOARDING] ?: false }

  val isSignedUp: Flow<Boolean> = prefs.data
    .map { it[IS_SIGNED_UP] ?: false }

  val guestActionCount: Flow<Int> = prefs.data
    .map { it[GUEST_ACTION_COUNT] ?: 0 }

  suspend fun markOnboardingSeen() {
    prefs.edit { it[HAS_SEEN_ONBOARDING] = true }
  }

  suspend fun incrementGuestActions() {
    prefs.edit { it[GUEST_ACTION_COUNT] = (it[GUEST_ACTION_COUNT] ?: 0) + 1 }
  }
}
```

### Soft Gate — Prompt at Moment of Value

```kotlin
// Show signup prompt after user completes N actions as a guest
@Composable
fun SoftSignupGate(
  guestActionCount: Int,
  threshold: Int = 3,
  onSignUp: () -> Unit,
  onDismiss: () -> Unit,
  content: @Composable () -> Unit,
) {
  content()

  if (guestActionCount >= threshold) {
    ModalBottomSheet(onDismissRequest = onDismiss) {
      Column(Modifier.padding(24.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
        Text("Save your progress", style = AppType.screenTitle)
        Text(
          "You've been busy. Create a free account to keep your data safe.",
          style = AppType.body,
        )
        NeuBrutButton("Create free account", onClick = onSignUp)
        TextButton(onClick = onDismiss) {
          Text("Keep using without an account", style = AppType.body)
        }
      }
    }
  }
}
```

### Contextual Permission Requests

```kotlin
// ❌ Don't request permissions on launch
LaunchedEffect(Unit) { locationPermissionLauncher.launch(permission) }

// ✓ Request at the moment the feature is used
@Composable
fun NearbyButton(onClick: () -> Unit) {
  val launcher = rememberLauncherForActivityResult(RequestPermission()) { granted ->
    if (granted) onClick()
  }
  NeuBrutButton("Find nearby") {
    launcher.launch(Manifest.permission.ACCESS_FINE_LOCATION)
  }
}
```

### Nav Graph Pattern

```kotlin
// Start in the app, not behind a login wall
NavHost(startDestination = if (isOnboarded) "home" else "welcome") {
  composable("welcome") {
    // Show value, skip button prominent, signup secondary
    WelcomeScreen(
      onSkip = { navController.navigate("home") },     // primary action
      onSignUp = { navController.navigate("signup") }, // secondary
    )
  }
  composable("home") { HomeScreen() }
  composable("signup") { SignupScreen() }
}
```

---

## Material 3 Theming

```kotlin
@Composable
fun AppTheme(darkTheme: Boolean = isSystemInDarkTheme(), content: @Composable () -> Unit) {
  val colorScheme = if (darkTheme) {
    darkColorScheme(primary = NeuBrut.Accent, background = NeuBrut.BgDark, surface = NeuBrut.BgDark)
  } else {
    lightColorScheme(primary = NeuBrut.Accent, background = NeuBrut.Bg, surface = NeuBrut.Bg)
  }
  MaterialTheme(colorScheme = colorScheme, typography = AppTypography, content = content)
}
```

---

## Navigation Compose

```kotlin
// Type-safe routes (Navigation 2.8+)
@Serializable object HomeRoute
@Serializable data class DetailRoute(val id: String)

NavHost(navController, startDestination = HomeRoute) {
  composable<HomeRoute> { HomeScreen() }
  composable<DetailRoute> { backStackEntry ->
    val route: DetailRoute = backStackEntry.toRoute()
    DetailScreen(id = route.id)
  }
}

// Navigate:
navController.navigate(DetailRoute(id = item.id))
navController.popBackStack()
```

---

## Lists: LazyColumn / LazyRow

```kotlin
LazyColumn(
  verticalArrangement = Arrangement.spacedBy(12.dp),
  contentPadding = PaddingValues(horizontal = 16.dp, vertical = 8.dp),
) {
  item { HeaderSection() }
  items(items = data, key = { it.id }) { item ->
    ItemCard(item = item)
  }
}
```

---

## Window Insets (Safe Areas)

```kotlin
// Activity.kt — always call this before setContent:
override fun onCreate(savedInstanceState: Bundle?) {
  super.onCreate(savedInstanceState)
  enableEdgeToEdge()
  setContent { AppTheme { AppNavHost() } }
}

// Scaffold handles insets automatically via innerPadding:
Scaffold { innerPadding ->
  LazyColumn(modifier = Modifier.padding(innerPadding)) { ... }
}

// Keyboard insets for input screens:
Column(
  modifier = Modifier
    .fillMaxSize()
    .imePadding()  // shifts content above keyboard
    .imeNestedScroll()
) { ... }
```

---

## ViewModel + StateFlow

```kotlin
data class ScreenUiState(
  val items: List<Item> = emptyList(),
  val isLoading: Boolean = false,
  val error: String? = null,
)

class ScreenViewModel(private val repo: ItemRepository) : ViewModel() {
  private val _state = MutableStateFlow(ScreenUiState())
  val state: StateFlow<ScreenUiState> = _state.asStateFlow()

  init { load() }

  fun load() = viewModelScope.launch {
    _state.update { it.copy(isLoading = true, error = null) }
    repo.getItems()
      .onSuccess { items -> _state.update { it.copy(items = items, isLoading = false) } }
      .onFailure { e -> _state.update { it.copy(error = e.message, isLoading = false) } }
  }
}
```

---

## Common Gotchas

- `Modifier` order matters — `padding().background()` ≠ `background().padding()`
- `remember` survives recomposition but NOT config changes — use `rememberSaveable` or ViewModel
- `LazyColumn` inside `Column` = infinite height crash — use `weight(1f)` on the `LazyColumn`
- `hardShadow` modifier must come BEFORE `border` and `background` in the modifier chain
- Shared element keys must be globally unique across the entire NavHost
- `animatedVisibilityScope` must be from the composable lambda (`this@composable`) not a parent
- `enableEdgeToEdge()` must be called before `setContent`
- `by` delegate needs `import androidx.compose.runtime.getValue` / `setValue`